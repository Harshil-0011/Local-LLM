from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import json
import base64
from fastapi.staticfiles import StaticFiles
from local_perplex.engine import LocalPerplex
import uvicorn
import os
import uuid
from pathlib import Path
from cachetools import TTLCache

# Set up paths relative to this file
app_dir = Path(__file__).parent
static_dir = app_dir / "static"
templates_dir = app_dir / "templates"

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

def split_filter(value, separator):
    return value.split(separator)

templates.env.filters["split"] = split_filter

engine = LocalPerplex()

# Server-side context cache with TTL to prevent memory leaks
# Contexts expire after 1 hour; max 100 concurrent contexts
context_cache = TTLCache(maxsize=100, ttl=3600)

@app.get("/api/status", response_class=JSONResponse)
async def api_status():
    """Check Ollama status and return available models."""
    status = engine.refresh_status()
    return {
        **status,
        "graph": engine.graph_stats()
    }

@app.get("/api/graph", response_class=JSONResponse)
async def api_graph():
    return {
        "stats": engine.graph_stats(),
        "recent_nodes": engine.graph.recent_nodes(limit=50)
    }

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    history = engine.history.get_all_sessions()
    docs = [f.name for f in engine.docs.doc_dir.glob("*") if f.is_file()]
    return templates.TemplateResponse(request, "index.html", {
        "history": history,
        "docs": docs,
        "current_model": engine.model,
        "ollama_online": engine.ollama_online,
        "available_models": engine.available_models,
        "graph_stats": engine.graph_stats()
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_get(request: Request):
    return templates.TemplateResponse(request, "settings.html", {
        "model": engine.model,
        "graph_stats": engine.graph_stats()
    })

@app.get("/graph", response_class=HTMLResponse)
async def graph_get(request: Request):
    return templates.TemplateResponse(request, "graph.html", {
        "stats": engine.graph_stats(),
        "nodes": engine.graph.recent_nodes(limit=100)
    })

@app.get("/history", response_class=HTMLResponse)
async def history_get(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "history": engine.history.get_all_sessions(),
        "docs": [f.name for f in engine.docs.doc_dir.glob("*") if f.is_file()],
        "current_model": engine.model,
        "ollama_online": engine.ollama_online,
        "available_models": engine.available_models,
        "graph_stats": engine.graph_stats()
    })

@app.get("/vault", response_class=HTMLResponse)
async def vault_get(request: Request):
    docs = []
    for f in engine.docs.doc_dir.glob("*"):
        if f.is_file():
            docs.append({
                "name": f.name,
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime
            })
    return templates.TemplateResponse(request, "vault.html", {"docs": docs})

@app.post("/vault/delete")
async def vault_delete(filename: str = Form(...)):
    safe_filename = os.path.basename(filename)
    filepath = engine.docs.doc_dir / safe_filename
    if filepath.exists() and filepath.is_file():
        filepath.unlink()
    return RedirectResponse(url="/vault", status_code=303)

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_get(request: Request):
    return templates.TemplateResponse(request, "privacy.html")

@app.post("/settings")
async def settings_post(model: str = Form(...)):
    engine.model = model
    return RedirectResponse(url="/", status_code=303)

@app.post("/upload-docs")
async def upload_docs(files: list[UploadFile] = File(...)):
    for file in files:
        content = await file.read()
        if not file.filename: continue
        safe_filename = os.path.basename(file.filename)
        fname = safe_filename.lower()
        if fname.endswith(('.pdf', '.docx', '.xlsx', '.csv')):
            with open(engine.docs.doc_dir / safe_filename, "wb") as f:
                f.write(content)
            engine.index_document(safe_filename)
        else:
            try:
                text = content.decode('utf-8')
                engine.docs.add_document(safe_filename, text)
                engine.graph.record_document(safe_filename, text)
            except Exception:
                continue
    return RedirectResponse(url="/vault", status_code=303)

@app.post("/ask", response_class=HTMLResponse)
async def ask(
    request: Request,
    question: str = Form(...),
    mode: str = Form("industry_standard"),
    focus_mode: str = Form("All"),
    conversation_history: str = Form(""),
    image: UploadFile = File(None),
    tag: str = Form("General"),
    privacy_mode: bool = Form(False)
):
    if mode not in {"industry_standard", "all_references", "pro"}:
        mode = "industry_standard"
    engine.refresh_status()

    # Check if Ollama is online
    if not engine.ollama_online:
        return templates.TemplateResponse(request, "result.html", {
            "question": question,
            "error": "Ollama is not running. Please start Ollama and refresh the page.",
            "sources": [],
            "sources_json": "[]",
            "mode": mode,
            "focus_mode": focus_mode,
            "conversation_history": conversation_history,
            "history_list": [],
            "context_session_id": "",
            "tag": tag,
            "privacy_mode": privacy_mode,
            "current_session_index": 0
        })
    
    history = []
    if conversation_history:
        try:
            history = json.loads(conversation_history)
        except json.JSONDecodeError:
            history = []

    image_b64 = None
    if image and image.filename:
        content = await image.read()
        image_b64 = base64.b64encode(content).decode('utf-8')

    # Step 1: Research (Fast or Deep)
    sources = []
    context = ""
    refined_q = question

    if mode == "pro":
        # In 'pro' mode, we'll stream research steps via the /stream-answer endpoint
        # The /ask endpoint just sets up the session
        pass
    else:
        refined_q, sources, context = engine.research_step(question, mode=mode, image_b64=image_b64, focus_mode=focus_mode)

    # Security: Privacy Mode Handling
    if privacy_mode:
        tag = "[INCOGNITO]"

    sources_json = json.dumps([{"title": s.title, "url": s.url, "relevance": s.relevance, "category": s.category, "content": s.content} for s in sources])

    # Generate a session ID to store the large context on the server
    session_id = str(uuid.uuid4())
    context_cache[session_id] = {
        "context": context,
        "sources_json": sources_json,
        "history_json": conversation_history,
        "focus_mode": focus_mode
    }

    return templates.TemplateResponse(request, "result.html", {
        "question": question,
        "sources": sources,
        "sources_json": sources_json,
        "mode": mode,
        "focus_mode": focus_mode,
        "conversation_history": conversation_history,
        "history_list": history,
        "context_session_id": session_id,
        "tag": tag,
        "privacy_mode": privacy_mode,
        "current_session_index": len(history)
    })

@app.get("/stream-answer")
async def stream_answer(question: str, session_id: str, mode: str, tag: str = "General"):
    # Check if Ollama is online
    if not engine.ollama_online:
        def error_generator():
            yield f"data: {json.dumps({'error': 'Ollama is not running. Please start Ollama to continue.'})}\n\n"
        return StreamingResponse(error_generator(), media_type="text/event-stream")
    
    cached = context_cache.get(session_id)
    if not cached:
        raise HTTPException(status_code=404, detail="Research session expired")

    history_json = cached["history_json"]
    try:
        history = json.loads(history_json) if history_json else []
    except json.JSONDecodeError:
        history = []
    focus_mode = cached.get("focus_mode", "All")

    def generator():
        final_sources = []
        final_context = ""

        try:
            if mode == "pro":
                # Deep Research Loop
                for step_type, data in engine.deep_research_iterative(question, mode=mode, focus_mode=focus_mode):
                    if step_type == "status":
                        yield f"data: {json.dumps({'status': data})}\n\n"
                    elif step_type == "result":
                        _, final_sources, final_context = data
                        # Update sources on the UI
                        sources_list = [{"title": s.title, "url": s.url, "relevance": s.relevance, "category": s.category, "content": s.content} for s in final_sources]
                        yield f"data: {json.dumps({'update_sources': sources_list})}\n\n"
            else:
                final_context = cached["context"]
                sources_data = json.loads(cached["sources_json"])
                from collections import namedtuple
                Source = namedtuple('Source', ['title', 'url', 'relevance', 'category', 'content'])
                final_sources = [Source(**s) for s in sources_data]

            full_answer = ""
            # Numerical citations need the source list
            for chunk in engine.ask_stream(question, final_context, history, mode, sources=final_sources):
                full_answer += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            # Finalize
            related = engine.finalize_research(question, full_answer, final_sources, tag)
            yield f"data: {json.dumps({'done': True, 'related': related})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Error during research: {str(e)}'})}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")

@app.get("/export/{index}", response_class=PlainTextResponse)
async def export_research(index: int):
    history = engine.history.get_all_sessions()
    if 0 <= index < len(history):
        session = history[index]
        report = f"# Research Report: {session['question']}\n\n"
        report += f"**Date:** {session['timestamp']}\n\n"
        report += "## Answer\n\n"
        report += session['answer'] + "\n\n"
        report += "## Sources\n\n"
        for s in session['sources']:
            report += f"- [{s['title']}]({s['url']}) (Relevance: {s['relevance']:.4f})\n"

        return report
    return "Session not found"

@app.get("/history/{index}", response_class=HTMLResponse)
async def view_history(request: Request, index: int):
    history = engine.history.get_all_sessions()
    if 0 <= index < len(history):
        session = history[index]
        return templates.TemplateResponse(request, "result.html", {
            "question": session["question"],
            "answer": session["answer"],
            "sources": session["sources"],
            "sources_json": json.dumps(session.get("sources", [])),
            "mode": "history",
            "focus_mode": "Saved",
            "conversation_history": "",
            "history_list": [],
            "context_session_id": "",
            "tag": session.get("tag", "General"),
            "privacy_mode": False,
            "current_session_index": index
        })
    return RedirectResponse(url="/", status_code=303)

def main():
    # Set max upload size to 10MB
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

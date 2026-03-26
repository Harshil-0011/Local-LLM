from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import html
from fastapi.staticfiles import StaticFiles
from local_perplex.engine import LocalPerplex
import uvicorn
import os
import uuid

app = FastAPI()
app.mount("/static", StaticFiles(directory="local_perplex/ui/web/static"), name="static")
templates = Jinja2Templates(directory="local_perplex/ui/web/templates")

def split_filter(value, separator):
    return value.split(separator)

templates.env.filters["split"] = split_filter

engine = LocalPerplex()

# Server-side context cache to avoid 414 URI Too Large errors
context_cache = {}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    history = engine.history.get_all_sessions()
    docs = [f.name for f in engine.docs.doc_dir.glob("*") if f.is_file()]
    return templates.TemplateResponse(request, "index.html", {
        "history": history,
        "docs": docs,
        "current_model": engine.model
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_get(request: Request):
    return templates.TemplateResponse(request, "settings.html", {"model": engine.model})

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
        else:
            try:
                text = content.decode('utf-8')
                engine.docs.add_document(safe_filename, text)
            except: continue
    return RedirectResponse(url="/", status_code=303)

@app.post("/ask", response_class=HTMLResponse)
async def ask(
    request: Request,
    question: str = Form(...),
    mode: str = Form(...),
    focus_mode: str = Form("All"),
    conversation_history: str = Form(""),
    image: UploadFile = File(None),
    tag: str = Form("General"),
    privacy_mode: bool = Form(False)
):
    # Security: Input Sanitization
    question = html.escape(question)
    tag = html.escape(tag)
    history = []
    if conversation_history:
        import json
        history = json.loads(conversation_history)

    image_b64 = None
    if image and image.filename:
        import base64
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

    import json
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
    import json
    cached = context_cache.get(session_id)
    if not cached:
        raise HTTPException(status_code=404, detail="Research session expired")

    history_json = cached["history_json"]
    history = json.loads(history_json) if history_json else []
    focus_mode = cached.get("focus_mode", "All")

    def generator():
        final_sources = []
        final_context = ""

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
            "current_session_index": index
        })
    return RedirectResponse(url="/", status_code=303)

def main():
    # Set max upload size to 10MB
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

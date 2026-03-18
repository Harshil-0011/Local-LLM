from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from local_perplex.engine import LocalPerplex
import uvicorn
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="local_perplex/ui/web/static"), name="static")
templates = Jinja2Templates(directory="local_perplex/ui/web/templates")
engine = LocalPerplex()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    history = engine.history.get_all_sessions()
    docs = [f.name for f in engine.docs.doc_dir.glob("*") if f.is_file()]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "history": history,
        "docs": docs,
        "current_model": engine.model
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_get(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request, "model": engine.model})

@app.post("/settings")
async def settings_post(model: str = Form(...)):
    engine.model = model
    return RedirectResponse(url="/", status_code=303)

@app.post("/upload-docs")
async def upload_docs(files: list[UploadFile] = File(...)):
    for file in files:
        content = await file.read()
        fname = file.filename.lower()
        if fname.endswith(('.pdf', '.docx', '.xlsx', '.csv')):
            with open(engine.docs.doc_dir / file.filename, "wb") as f:
                f.write(content)
        else:
            try:
                text = content.decode('utf-8')
                engine.docs.add_document(file.filename, text)
            except: continue
    return RedirectResponse(url="/", status_code=303)

@app.post("/ask", response_class=HTMLResponse)
async def ask(request: Request, question: str = Form(...), mode: str = Form(...), focus_mode: str = Form("All"), conversation_history: str = Form(""), image: UploadFile = File(None), tag: str = Form("General")):
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
    if mode == "pro":
        refined_q, sources, context = engine.deep_research_step(question, mode=mode)
    else:
        refined_q, sources, context = engine.research_step(question, mode=mode, image_b64=image_b64, focus_mode=focus_mode)

    return templates.TemplateResponse("result.html", {
        "request": request,
        "question": question,
        "sources": sources,
        "mode": mode,
        "focus_mode": focus_mode,
        "conversation_history": conversation_history,
        "history_list": history,
        "context_for_stream": context,
        "tag": tag
    })

@app.get("/stream-answer")
async def stream_answer(question: str, context: str, mode: str, history_json: str = "", tag: str = "General"):
    import json
    history = json.loads(history_json) if history_json else []

    def generator():
        full_answer = ""
        for chunk in engine.ask_stream(question, context, history, mode):
            full_answer += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        # Finalize
        related = engine.finalize_research(question, full_answer, [], tag) # Simplified sources for now
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
        return templates.TemplateResponse("result.html", {
            "request": request,
            "question": session["question"],
            "answer": session["answer"],
            "sources": session["sources"]
        })
    return RedirectResponse(url="/", status_code=303)

def main():
    # Set max upload size to 10MB
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
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
    return templates.TemplateResponse("index.html", {"request": request, "history": history})

@app.post("/ask", response_class=HTMLResponse)
def ask(request: Request, question: str = Form(...), mode: str = Form(...), conversation_history: str = Form("")):
    history = []
    if conversation_history:
        import json
        history = json.loads(conversation_history)

    answer, sources, related = engine.ask(question, mode=mode, history=history)

    # Update history for next follow-up
    history.append({"question": question, "answer": answer})
    import json
    new_history_json = json.dumps(history)

    return templates.TemplateResponse("result.html", {
        "request": request,
        "question": question,
        "answer": answer,
        "sources": sources,
        "mode": mode,
        "conversation_history": new_history_json,
        "history_list": history,
        "related": related
    })

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
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

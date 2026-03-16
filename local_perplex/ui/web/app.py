from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
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
def ask(request: Request, question: str = Form(...), mode: str = Form(...)):
    answer, sources = engine.ask(question, mode=mode)
    return templates.TemplateResponse("result.html", {
        "request": request,
        "question": question,
        "answer": answer,
        "sources": sources
    })

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

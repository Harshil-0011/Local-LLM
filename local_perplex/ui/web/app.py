from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from local_perplex.engine import LocalPerplex
import uvicorn
import os

app = FastAPI()
templates = Jinja2Templates(directory="local_perplex/ui/web/templates")
engine = LocalPerplex()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask", response_class=HTMLResponse)
def ask(request: Request, question: str = Form(...), mode: str = Form(...)):
    answer, sources = engine.ask(question, mode=mode)
    return templates.TemplateResponse("result.html", {
        "request": request,
        "question": question,
        "answer": answer,
        "sources": sources
    })

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from urllib.parse import quote_plus
import uvicorn
import os

from ...config import get_config
from ...interview.manager import InterviewManager
from ...spec.builder import SpecBuilder
from ...codegen.generator import CodeGenerator

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Load config
config = get_config()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "config": config})

@app.get("/interview", response_class=HTMLResponse)
async def interview_get(request: Request, output_dir: str = None):
    out = Path(output_dir or config.default_output_dir)
    manager = InterviewManager(out)
    return templates.TemplateResponse("interview.html", {
        "request": request,
        "questions": manager.get_questions(),
        "answers": manager.answers,
        "output_dir": str(out)
    })

@app.post("/interview")
async def interview_post(request: Request):
    form_data = await request.form()
    output_dir = form_data.get("output_dir")
    out = Path(output_dir)
    manager = InterviewManager(out)

    for q in manager.get_questions():
        val = form_data.get(q['id'])
        if val is not None:
            manager.update_answer(q['id'], val)

    return RedirectResponse(url=f"/spec?output_dir={quote_plus(str(output_dir))}", status_code=303)

@app.get("/spec", response_class=HTMLResponse)
async def spec_get(request: Request, output_dir: str):
    out = Path(output_dir)
    spec_file = out / "project_spec.md"
    spec_content = ""
    if spec_file.exists():
        with open(spec_file, "r", encoding="utf-8") as f:
            spec_content = f.read()

    return templates.TemplateResponse("spec.html", {
        "request": request,
        "output_dir": output_dir,
        "spec_content": spec_content
    })

@app.post("/build-spec")
async def build_spec_post(output_dir: str = Form(...)):
    out = Path(output_dir)
    manager = InterviewManager(out)
    builder = SpecBuilder(config.ollama_base_url, config.planner_model)
    spec_content = builder.build_spec(manager.answers)
    builder.save_spec(out, spec_content)
    return RedirectResponse(url=f"/spec?output_dir={quote_plus(str(output_dir))}", status_code=303)

@app.get("/codegen", response_class=HTMLResponse)
async def codegen_get(request: Request, output_dir: str):
    return templates.TemplateResponse("codegen.html", {
        "request": request,
        "output_dir": output_dir
    })

@app.post("/generate-code")
async def generate_code_post(output_dir: str = Form(...)):
    out = Path(output_dir)
    spec_file = out / "project_spec.md"
    with open(spec_file, "r", encoding="utf-8") as f:
        spec_content = f.read()

    generator = CodeGenerator(config.ollama_base_url, config.coder_model)
    llm_output = generator.generate_code(spec_content)
    generator.parse_and_save(out, llm_output)
    return RedirectResponse(url=f"/codegen?output_dir={quote_plus(str(output_dir))}", status_code=303)

@app.get("/settings", response_class=HTMLResponse)
async def settings_get(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request, "config": config})

@app.post("/settings")
async def settings_post(
    ollama_base_url: str = Form(...),
    planner_model: str = Form(...),
    coder_model: str = Form(...),
    default_output_dir: str = Form(...)
):
    global config
    config.ollama_base_url = ollama_base_url
    config.planner_model = planner_model
    config.coder_model = coder_model
    config.default_output_dir = default_output_dir
    config.save()
    return RedirectResponse(url="/settings", status_code=303)

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

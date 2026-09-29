import os
import logging
from typing import Optional
from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf

logger = logging.getLogger(__name__)

router = APIRouter()

# Locate templates directory relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

class PromptRequest(BaseModel):
    prompt: str = Field(..., description="Main story premise or plot idea")
    character_name: Optional[str] = Field("Hero", description="Protagonist name")
    setting: Optional[str] = Field("Metropolis", description="Story environment / backdrop")
    tone: Optional[str] = Field("Action-Packed", description="Tone and emotional style")
    style: Optional[str] = Field("Modern Graphic Novel", description="Art and illustration style")

def _run_comic_pipeline(prompt: str, character_name: str, setting: str, tone: str, style: str):
    """
    Executes the 5-step comic generation pipeline:
    1. generate_outline
    2. generate_story
    3. generate_image (loop of 5)
    4. build_comic_layout
    5. save_pdf
    """
    # Combine parameters into a single string full_prompt
    full_prompt = (
        f"Story Concept: {prompt}. "
        f"Main Character: {character_name}. "
        f"Setting: {setting}. "
        f"Tone: {tone}. "
        f"Art Style: {style}."
    )
    logger.info("Executing comic pipeline with prompt: %s", full_prompt)

    # 1. Generate outline with Gemini 1.5 Flash
    outline = generate_outline(full_prompt)

    # 2. Generate script / story with Gemini 1.5 Pro
    full_story = generate_story(outline)

    # 3. Generate image per panel in loop
    image_paths = []
    for idx, panel in enumerate(outline, start=1):
        panel_prompt = panel.get("image_prompt", "")
        # Augment with style information
        styled_image_prompt = f"{panel_prompt}, in {style} art style, comic illustration, vibrant inks"
        panel_filename = f"panel_{idx}_{character_name.lower().replace(' ', '_')}"
        img_path = generate_image(prompt=styled_image_prompt, filename=panel_filename)
        image_paths.append(img_path)

    # 4. Build comic layout
    layout = build_comic_layout(image_paths=image_paths, full_story=full_story, outline=outline)

    # 5. Save multi-page PDF
    web_pdf_path = save_pdf(layout)

    return layout, web_pdf_path

@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Renders the ComicCraft studio home form."""
    return templates.TemplateResponse(request=request, name="index.html")

@router.post("/generate", response_class=HTMLResponse)
async def post_generate(
    request: Request,
    prompt: str = Form(...),
    character_name: str = Form("Hero"),
    setting: str = Form("Futuristic Metropolis"),
    tone: str = Form("Action-Packed"),
    style: str = Form("Modern Graphic Novel")
):
    """
    Accepts HTML form inputs, runs full generation sequence, and renders comic preview.
    """
    layout, web_pdf_path = _run_comic_pipeline(
        prompt=prompt,
        character_name=character_name,
        setting=setting,
        tone=tone,
        style=style
    )

    return templates.TemplateResponse(
        request=request,
        name="comic_preview.html",
        context={
            "layout": layout,
            "web_pdf_path": web_pdf_path,
            "prompt": prompt,
            "character_name": character_name,
            "setting": setting,
            "tone": tone,
            "style": style
        }
    )

@router.post("/generate-comic/json")
async def post_generate_json(req: PromptRequest):
    """
    Accepts Pydantic model PromptRequest, executes AI generation workflow,
    and returns JSON payload containing layout data and PDF export path.
    """
    layout, web_pdf_path = _run_comic_pipeline(
        prompt=req.prompt,
        character_name=req.character_name or "Hero",
        setting=req.setting or "Metropolis",
        tone=req.tone or "Action-Packed",
        style=req.style or "Modern Graphic Novel"
    )

    return JSONResponse(
        content={
            "status": "success",
            "pdf_path": web_pdf_path,
            "layout": layout
        }
    )

@router.get("/export-success", response_class=HTMLResponse)
async def get_export_success(request: Request, pdf_path: str = Query(...)):
    """Renders download confirmation page with PDF link."""
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_path": pdf_path
        }
    )

@router.get("/test-image")
async def get_test_image(prompt: str = Query("Action superhero hero pose, comic book style")):
    """Executes generate_image() directly for isolated debugging."""
    img_path = generate_image(prompt=prompt)
    return JSONResponse(
        content={
            "status": "success",
            "prompt": prompt,
            "image_path": img_path
        }
    )

import os
import re
import time
import uuid
import logging
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Global cache for Stable Diffusion pipeline
_sd_pipeline = None

def _sanitize_filename(prompt: str) -> str:
    """Sanitizes prompt into a safe, valid filesystem filename."""
    clean = re.sub(r'[^a-zA-Z0-9_\- ]', '', prompt)
    clean = clean.strip().replace(' ', '_')[:32]
    timestamp = int(time.time() * 1000) % 1000000
    if not clean:
        clean = "panel"
    return f"{clean}_{timestamp}_{uuid.uuid4().hex[:4]}"

def _render_styled_comic_card(prompt: str, output_path: str, width: int = 512, height: int = 512):
    """
    Renders an eye-catching comic-book style visual panel card.
    Used when diffusers is operating in mock/fallback mode or running on CPU/offline.
    """
    img = Image.new("RGB", (width, height), color=(20, 24, 38))
    draw = ImageDraw.Draw(img)

    # Dynamic color palette based on prompt hash
    colors = [
        ((255, 69, 58), (255, 159, 10)),   # Red to Orange Action
        ((48, 209, 88), (50, 173, 230)),   # Green to Cyan Sci-Fi
        ((88, 86, 214), (175, 82, 222)),   # Indigo to Purple Mystery
        ((255, 214, 10), (255, 107, 107)), # Golden Comic Pop
        ((10, 132, 255), (94, 92, 230))    # Electric Blue Heroic
    ]
    color_pair = colors[abs(hash(prompt)) % len(colors)]
    c1, c2 = color_pair

    # Draw comic gradient background
    for y in range(height):
        ratio = y / float(height)
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Comic halftone / speedlines effect
    for i in range(0, width + height, 24):
        draw.line([(i, 0), (0, i)], fill=(255, 255, 255, 40), width=1)

    # Comic inner frame
    border_margin = 16
    draw.rectangle(
        [(border_margin, border_margin), (width - border_margin, height - border_margin)],
        outline=(255, 255, 255),
        width=4
    )
    draw.rectangle(
        [(border_margin + 6, border_margin + 6), (width - border_margin - 6, height - border_margin - 6)],
        outline=(0, 0, 0),
        width=2
    )

    # Sound effect starburst / pop burst in center
    cx, cy = width // 2, height // 2 - 30
    burst_radius = 85
    burst_points = []
    import math
    for i in range(16):
        angle = i * (math.pi / 8)
        r = burst_radius if i % 2 == 0 else burst_radius * 0.55
        px = cx + int(r * math.cos(angle))
        py = cy + int(r * math.sin(angle))
        burst_points.append((px, py))
    draw.polygon(burst_points, fill=(255, 255, 255), outline=(0, 0, 0))

    # Caption box at bottom
    box_top = height - 130
    draw.rectangle(
        [(border_margin + 12, box_top), (width - border_margin - 12, height - border_margin - 12)],
        fill=(255, 255, 255),
        outline=(0, 0, 0),
        width=3
    )

    # Text wrapping for prompt summary
    words = prompt.split()
    lines = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > 38:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    lines = lines[:3]  # keep at most 3 lines

    # Try loading custom font or fallback to default
    font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "fonts", "DejaVuSans-Bold.ttf")
    font = None
    if os.path.exists(font_path):
        try:
            font = ImageFont.truetype(font_path, 13)
            burst_font = ImageFont.truetype(font_path, 22)
        except Exception:
            font = None
            burst_font = None

    if burst_font:
        draw.text((cx - 30, cy - 14), "POW!", fill=(255, 59, 48), font=burst_font)
    else:
        draw.text((cx - 15, cy - 8), "POW!", fill=(255, 59, 48))

    ty = box_top + 10
    for line in lines:
        if font:
            draw.text((border_margin + 20, ty), line, fill=(10, 10, 10), font=font)
        else:
            draw.text((border_margin + 20, ty), line, fill=(10, 10, 10))
        ty += 18

    img.save(output_path, "PNG")

def generate_image(prompt: str, filename: str = None) -> str:
    """
    Generates an image for a comic panel using the Diffusers pipeline with 'runwayml/stable-diffusion-v1-5'.
    Saves image to static/panels/{filename}.png and returns the path.
    """
    global _sd_pipeline

    # 1. Sanitize the prompt to create a clean filename if not provided
    if not filename:
        clean_name = _sanitize_filename(prompt)
    else:
        clean_name = filename.replace(".png", "")
        clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', clean_name)

    # 3. Ensure directory static/panels/ exists
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, "static", "panels")
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"{clean_name}.png")
    relative_path = f"static/panels/{clean_name}.png"

    # Check for mock flag
    use_mock = os.getenv("USE_MOCK_IMAGE_GEN", "false").strip().lower() == "true"
    if use_mock:
        logger.info("USE_MOCK_IMAGE_GEN is enabled. Generating stylized comic panel.")
        _render_styled_comic_card(prompt, file_path)
        return relative_path

    # 2. Pass prompt to Stable Diffusion pipeline: pipe(prompt).images[0]
    try:
        if _sd_pipeline is None:
            logger.info("Initializing StableDiffusionPipeline with 'runwayml/stable-diffusion-v1-5'...")
            from diffusers import StableDiffusionPipeline
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if device == "cuda" else torch.float32
            
            _sd_pipeline = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch_dtype
            )
            _sd_pipeline = _sd_pipeline.to(device)

        # Generate image
        image = _sd_pipeline(prompt).images[0]
        # 4. Save the image to static/panels/{filename}.png and return string path
        image.save(file_path)
        logger.info("Saved diffusers panel image to %s", file_path)
        return relative_path

    except Exception as exc:
        logger.warning(
            "Diffusers pipeline execution encountered an issue (%s). "
            "Falling back to stylized comic panel generation.", exc
        )
        _render_styled_comic_card(prompt, file_path)
        return relative_path

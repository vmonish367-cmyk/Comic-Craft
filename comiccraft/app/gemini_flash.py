import os
import json
import re
import logging
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are a professional AI comic planner. Your task is to plan an exciting, cohesive, "
    "5-panel comic book based on the user's prompt. You must output ONLY a valid, raw JSON array "
    "containing exactly 5 panel objects. Do NOT include markdown code blocks, backticks, or explanatory text.\n"
    "Each object must have these exact keys:\n"
    "- 'panel': integer (1 to 5)\n"
    "- 'title': short punchy title string for the panel\n"
    "- 'scene_description': rich visual description of what happens in the panel\n"
    "- 'image_prompt': detailed descriptive visual prompt suitable for AI image generation (style, characters, lighting, composition)"
)

def _get_fallback_outline(user_prompt: str, reason: str = "") -> list:
    """Provides a safe, structured 5-panel fallback outline if generation or parsing fails."""
    logger.warning("Using fallback outline. Reason: %s", reason)
    clean_topic = user_prompt.strip()[:60] if user_prompt else "The Journey Begins"
    return [
        {
            "panel": 1,
            "title": "The Awakening",
            "scene_description": f"The story begins as our hero steps forward into the unknown. Context: {clean_topic}.",
            "image_prompt": f"Dramatic comic book panel, wide shot, cinematic lighting, vibrant ink art introducing: {clean_topic}, retro pop-art colors, detailed comic background"
        },
        {
            "panel": 2,
            "title": "The Inciting Incident",
            "scene_description": "A sudden disturbance breaks the silence. A high-stakes discovery or challenge appears.",
            "image_prompt": f"Medium angle comic illustration, high tension, glowing energy or ominous shadow confronting the protagonist, dynamic superhero comic style"
        },
        {
            "panel": 3,
            "title": "Rising Stakes",
            "scene_description": "The protagonist confronts the threat head-on, testing their resolve and skills.",
            "image_prompt": "Action-packed dynamic comic frame, bold motion lines, intense character expression, dramatic perspective, detailed graphic novel artwork"
        },
        {
            "panel": 4,
            "title": "The Climax",
            "scene_description": "The turning point of the conflict. Everything hangs in the balance as power surges.",
            "image_prompt": "Epic climactic comic book splash frame, vibrant explosive colors, high contrast ink lines, heroic pose, breathtaking visual spectacle"
        },
        {
            "panel": 5,
            "title": "The New Dawn",
            "scene_description": "The dust settles, revealing victory and a renewed sense of purpose.",
            "image_prompt": "Inspiring closing comic panel, golden hour warm lighting, triumphant character standing tall, cinematic vista in background"
        }
    ]

def generate_outline(user_prompt: str) -> list:
    """
    Generates a 5-panel comic outline using Google Gemini 1.5 Flash.
    Returns a list of 5 dictionaries with keys: panel, title, scene_description, image_prompt.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() in ("", "your_gemini_api_key_here"):
        logger.info("GEMINI_API_KEY not configured. Falling back to default structured outline.")
        return _get_fallback_outline(user_prompt, reason="GEMINI_API_KEY missing or placeholder")

    try:
        genai.configure(api_key=api_key.strip())
        
        # Use gemini-1.5-flash as specified
        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-flash",
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        prompt_text = (
            f"Generate a 5-panel comic outline for the following story prompt:\n\n{user_prompt}\n\n"
            "Respond ONLY with a strictly formatted JSON array containing 5 panel objects. "
            "Keys required: 'panel' (int 1-5), 'title' (str), 'scene_description' (str), 'image_prompt' (str)."
        )

        response = model.generate_content(
            prompt_text,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7
            )
        )
        
        raw_text = response.text.strip() if response.text else ""
        
        # Strip markdown backticks if present
        clean_json = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
        clean_json = re.sub(r"\s*```$", "", clean_json)
        clean_json = clean_json.strip()

        # Parse JSON
        parsed = json.loads(clean_json)

        # Validate that output is a list of dictionaries with all mandatory keys
        if not isinstance(parsed, list) or len(parsed) != 5:
            raise ValueError(f"Expected a list of exactly 5 panels, got {type(parsed)} of length {len(parsed) if isinstance(parsed, list) else 0}")

        mandatory_keys = {"panel", "title", "scene_description", "image_prompt"}
        validated = []
        for idx, item in enumerate(parsed, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"Panel item {idx} is not a dictionary")
            if not mandatory_keys.issubset(item.keys()):
                missing = mandatory_keys - item.keys()
                raise ValueError(f"Panel item {idx} is missing keys: {missing}")
            
            validated.append({
                "panel": int(item.get("panel", idx)),
                "title": str(item.get("title", f"Panel {idx}")).strip(),
                "scene_description": str(item.get("scene_description", "")).strip(),
                "image_prompt": str(item.get("image_prompt", "")).strip()
            })

        return validated

    except Exception as exc:
        logger.error("Error generating outline with Gemini 1.5 Flash: %s", exc)
        return _get_fallback_outline(user_prompt, reason=str(exc))

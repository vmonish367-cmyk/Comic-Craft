import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are a professional comic book writer. Your task is to write engaging, punchy comic book "
    "narration, captions, and character dialogue for a 5-panel comic based on the provided outline.\n"
    "Format each panel strictly with bold panel headers and clear labels:\n"
    "**Panel X: [Panel Title]**\n"
    "**CAPTION:** [Descriptive comic caption]\n"
    "**NARRATION:** [Comic narration setting the mood]\n"
    "**[CHARACTER NAME]:** \"[Dialogue lines]\"\n\n"
    "Maintain consistent character voices, exciting comic pacing, and dramatic tension."
)

def _get_fallback_story(outline: list) -> str:
    """Fallback story generation when Gemini 1.5 Pro cannot be contacted."""
    panels_text = []
    for item in outline:
        num = item.get("panel", 1)
        title = item.get("title", f"Panel {num}")
        desc = item.get("scene_description", "An intriguing moment unfolds.")
        panel_block = (
            f"**Panel {num}: {title}**\n"
            f"**CAPTION:** {desc}\n"
            f"**NARRATION:** The stakes escalate as fate takes a dramatic turn in this chapter.\n"
            f"**HERO:** \"There is no turning back now. We push forward!\""
        )
        panels_text.append(panel_block)
    return "\n\n".join(panels_text)

def generate_story(outline: list) -> str:
    """
    Takes a 5-panel outline list and generates a full comic script with dialogue and narration
    using Google Gemini 1.5 Pro.
    Returns the formatted story string with '**Panel X: Title**' headers.
    """
    # Format outline into a clean numbered string representation
    outline_representation_lines = []
    for p in outline:
        p_num = p.get("panel", "")
        p_title = p.get("title", "")
        p_desc = p.get("scene_description", "")
        p_prompt = p.get("image_prompt", "")
        outline_representation_lines.append(
            f"Panel {p_num}: {p_title}\n"
            f"  Scene: {p_desc}\n"
            f"  Visual Tone: {p_prompt}"
        )
    formatted_outline = "\n\n".join(outline_representation_lines)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() in ("", "your_gemini_api_key_here"):
        logger.info("GEMINI_API_KEY not configured. Using structured fallback story.")
        return _get_fallback_story(outline)

    try:
        genai.configure(api_key=api_key.strip())
        
        # Use gemini-1.5-pro as specified
        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-pro",
            system_instruction=SYSTEM_INSTRUCTION
        )

        user_prompt = (
            "Here is the 5-panel comic outline:\n\n"
            f"{formatted_outline}\n\n"
            "Please write the full script for these 5 panels. "
            "Ensure you start each panel with '**Panel 1: [Title]**', '**Panel 2: [Title]**', etc., "
            "and include '**CAPTION:**', '**NARRATION:**', and character dialogues for every panel."
        )

        response = model.generate_content(
            user_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.75,
                max_output_tokens=2048
            )
        )

        if response.text and response.text.strip():
            story_text = response.text.strip()
            # Verify that the response includes panel headers
            if "**Panel" in story_text or "**Panel 1" in story_text:
                return story_text
            else:
                logger.warning("Gemini Pro output lacked expected panel markers, using fallback.")
                return _get_fallback_story(outline)
        else:
            return _get_fallback_story(outline)

    except Exception as exc:
        logger.error("Error generating story with Gemini 1.5 Pro: %s", exc)
        return _get_fallback_story(outline)

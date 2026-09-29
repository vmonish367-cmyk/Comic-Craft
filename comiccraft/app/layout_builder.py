import re
import logging

logger = logging.getLogger(__name__)

def build_comic_layout(image_paths: list, full_story: str, outline: list) -> list:
    """
    Builds the structured comic layout for Jinja2 template and PDF generation.
    
    Logic:
      1. Split full_story using '**Panel' delimiters.
      2. Iterate sequentially over (image_paths, story_panels, outline) using zip.
      3. Extract 'panel', 'title', 'image_path', 'text' (narrative/dialogue text stripped of panel title lines),
         and 'scene_description'.
      4. Return a list of dictionary panel layouts ready for Jinja2 rendering.
    """
    # 1. Split full_story using "**Panel" delimiters
    raw_splits = full_story.split("**Panel")
    story_panels = []
    
    for segment in raw_splits:
        segment = segment.strip()
        if not segment:
            continue
        
        # Segment typically starts with e.g. " 1: The Awakening**\n**CAPTION:**..."
        # or " 1 - Title\n..."
        lines = segment.splitlines()
        first_line = lines[0].strip() if lines else ""
        
        # Extract title line and remaining text
        # Remove trailing bold markers or colons from first line
        title_candidate = re.sub(r'^\s*\d+[\s:\-]*', '', first_line)
        title_candidate = title_candidate.replace('**', '').strip()
        
        # Strip panel title line to obtain narrative/dialogue text
        remaining_lines = lines[1:] if len(lines) > 1 else []
        narrative_text = "\n".join(remaining_lines).strip()
        
        story_panels.append({
            "title": title_candidate,
            "text": narrative_text
        })

    # If splitting resulted in fewer story panels than outline, pad with fallback
    while len(story_panels) < len(outline):
        idx = len(story_panels)
        story_panels.append({
            "title": outline[idx].get("title", f"Panel {idx + 1}"),
            "text": "**CAPTION:** " + outline[idx].get("scene_description", "The story continues...")
        })

    layout = []
    # 2. Iterate sequentially over (image_paths, story_panels, outline) using zip
    for idx, (img_path, story_data, outline_item) in enumerate(zip(image_paths, story_panels, outline), start=1):
        panel_num = outline_item.get("panel", idx)
        
        # Fall back to outline title if story title extraction was empty
        title = story_data["title"] if story_data["title"] else outline_item.get("title", f"Panel {panel_num}")
        scene_desc = outline_item.get("scene_description", "")
        img_prompt = outline_item.get("image_prompt", "")
        
        text_content = story_data["text"]
        if not text_content:
            text_content = f"**CAPTION:** {scene_desc}"

        # 3. Extract required dictionary fields
        panel_dict = {
            "panel": panel_num,
            "title": title,
            "image_path": img_path,
            "text": text_content,
            "scene_description": scene_desc,
            "image_prompt": img_prompt
        }
        layout.append(panel_dict)

    # 4. Return list of dictionary panel layouts ready for Jinja2 rendering
    return layout

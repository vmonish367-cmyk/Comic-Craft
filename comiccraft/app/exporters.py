import os
import re
from datetime import datetime
import logging
from fpdf import FPDF

logger = logging.getLogger(__name__)

class ComicPDF(FPDF):
    def footer(self):
        # Position cursor at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font("DejaVu", "", 9)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"ComicCraft  |  Page {self.page_no()}", align="C")

def save_pdf(layout: list) -> str:
    """
    Exports the 5-panel comic layout to a multi-page PDF using FPDF and DejaVu Unicode font.
    
    Logic:
      1. Loop through each panel in the layout list and create a new page (pdf.add_page()).
      2. Render the panel header centered.
      3. Render the panel image (located at image_path) at y=30 with height=100.
      4. Render text content directly below the image with spacing.
      5. Save the generated file to static/exports/ with timestamped naming (e.g., comic_YYYYMMDDHHMMSS.pdf).
      6. Return the saved PDF file path.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    exports_dir = os.path.join(base_dir, "static", "exports")
    fonts_dir = os.path.join(base_dir, "static", "fonts")
    os.makedirs(exports_dir, exist_ok=True)

    pdf = ComicPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    # Register DejaVu fonts for full Unicode safety
    regular_font = os.path.join(fonts_dir, "DejaVuSans.ttf")
    bold_font = os.path.join(fonts_dir, "DejaVuSans-Bold.ttf")

    if os.path.exists(regular_font):
        pdf.add_font("DejaVu", "", regular_font)
    else:
        pdf.add_font("DejaVu", "", "")

    if os.path.exists(bold_font):
        pdf.add_font("DejaVu", "B", bold_font)
    else:
        pdf.add_font("DejaVu", "B", regular_font if os.path.exists(regular_font) else "")

    # 1. Loop through each panel in layout list and create a new page
    for panel_item in layout:
        pdf.add_page()
        panel_num = panel_item.get("panel", 1)
        panel_title = panel_item.get("title", f"Panel {panel_num}")
        image_path = panel_item.get("image_path", "")
        text_content = panel_item.get("text", "")
        scene_desc = panel_item.get("scene_description", "")

        # 2. Render the panel header centered
        pdf.set_y(15)
        pdf.set_font("DejaVu", "B", 18)
        pdf.set_text_color(20, 20, 20)
        header_text = f"Panel {panel_num}: {panel_title}"
        pdf.cell(0, 10, header_text, align="C", new_x="LMARGIN", new_y="NEXT")

        # 3. Render the panel image (located at image_path) at y=30 with height=100
        # Resolve absolute path of image
        abs_image_path = image_path
        if not os.path.isabs(abs_image_path):
            abs_image_path = os.path.join(base_dir, image_path)

        if os.path.exists(abs_image_path):
            # Center a 100mm wide/high image on A4 (width 210mm: (210 - 100) / 2 = 55mm)
            img_x = 55
            img_y = 30
            img_h = 100
            pdf.image(abs_image_path, x=img_x, y=img_y, h=img_h)
            
            # Subtle comic border around image in PDF
            pdf.set_draw_color(40, 40, 40)
            pdf.set_line_width(0.6)
            pdf.rect(img_x, img_y, img_h, img_h)

        # 4. Render text content directly below the image with spacing
        pdf.set_y(136)

        # Scene description sub-bar
        if scene_desc:
            pdf.set_font("DejaVu", "", 10)
            pdf.set_text_color(90, 90, 100)
            pdf.multi_cell(0, 6, f"Scene: {scene_desc}", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        # Narrative / dialogue text
        if text_content:
            pdf.set_text_color(15, 15, 20)
            
            # Process story lines
            story_lines = text_content.strip().splitlines()
            for line in story_lines:
                clean_line = line.strip()
                if not clean_line:
                    pdf.ln(2)
                    continue

                # Distinguish Caption / Narration / Dialogue
                if clean_line.startswith("**CAPTION:**") or "CAPTION:" in clean_line:
                    display_text = clean_line.replace("**CAPTION:**", "CAPTION:").replace("**", "")
                    pdf.set_font("DejaVu", "B", 10.5)
                    pdf.set_text_color(180, 80, 0) # Comic orange-gold
                    pdf.multi_cell(0, 6, display_text, new_x="LMARGIN", new_y="NEXT")
                elif clean_line.startswith("**NARRATION:**") or "NARRATION:" in clean_line:
                    display_text = clean_line.replace("**NARRATION:**", "NARRATION:").replace("**", "")
                    pdf.set_font("DejaVu", "", 10.5)
                    pdf.set_text_color(40, 40, 60)
                    pdf.multi_cell(0, 6, display_text, new_x="LMARGIN", new_y="NEXT")
                else:
                    # Dialogue or general narration
                    display_text = clean_line.replace("**", "")
                    pdf.set_font("DejaVu", "", 10.5)
                    pdf.set_text_color(10, 10, 10)
                    pdf.multi_cell(0, 6, display_text, new_x="LMARGIN", new_y="NEXT")

    # 5. Save the generated file to static/exports/ with timestamped naming
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    pdf_filename = f"comic_{timestamp}.pdf"
    full_pdf_path = os.path.join(exports_dir, pdf_filename)
    pdf.output(full_pdf_path)
    logger.info("Generated PDF exported to %s", full_pdf_path)

    # 6. Return saved PDF file path (relative for web serving)
    web_pdf_path = f"static/exports/{pdf_filename}"
    return web_pdf_path

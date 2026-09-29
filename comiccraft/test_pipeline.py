import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure comiccraft directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf
from app.main import app

class TestComicCraftPipeline(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_gemini_flash_outline(self):
        """Test that generate_outline returns 5 valid panel dictionaries."""
        outline = generate_outline("A brave cybernetic detective in futuristic Neo-Tokyo")
        self.assertIsInstance(outline, list, "Outline should be a list")
        self.assertEqual(len(outline), 5, "Outline must contain exactly 5 panels")
        for item in outline:
            self.assertIn("panel", item)
            self.assertIn("title", item)
            self.assertIn("scene_description", item)
            self.assertIn("image_prompt", item)
            self.assertIsInstance(item["panel"], int)
            self.assertTrue(1 <= item["panel"] <= 5)

    def test_02_gemini_pro_story(self):
        """Test that generate_story generates story with panel delimiters."""
        outline = [
            {"panel": 1, "title": "The Awakening", "scene_description": "Intro scene", "image_prompt": "Hero waking up"},
            {"panel": 2, "title": "The Threat", "scene_description": "A monster looms", "image_prompt": "Giant shadow"},
            {"panel": 3, "title": "Battle Lines", "scene_description": "Clash begins", "image_prompt": "Action strike"},
            {"panel": 4, "title": "Peak Strike", "scene_description": "Max power", "image_prompt": "Electric surge"},
            {"panel": 5, "title": "Victory", "scene_description": "Peace restored", "image_prompt": "Sunset hero"}
        ]
        story = generate_story(outline)
        self.assertIsInstance(story, str)
        self.assertIn("**Panel", story, "Story must contain '**Panel' delimiters")

    def test_03_image_generator(self):
        """Test generate_image creates an image in static/panels/."""
        img_path = generate_image(prompt="Comic hero soaring above clouds", filename="test_panel_1")
        self.assertTrue(img_path.startswith("static/panels/"))
        abs_path = os.path.join(CURRENT_DIR, img_path)
        self.assertTrue(os.path.exists(abs_path), f"File {abs_path} should exist")
        self.assertGreater(os.path.getsize(abs_path), 0, "Image file should not be empty")

    def test_04_layout_builder(self):
        """Test build_comic_layout correctly zips and extracts fields."""
        image_paths = [f"static/panels/test_panel_{i}.png" for i in range(1, 6)]
        for p in image_paths:
            # create empty or test file if not existing
            abs_p = os.path.join(CURRENT_DIR, p)
            if not os.path.exists(abs_p):
                with open(abs_p, "wb") as f:
                    f.write(b"dummy")

        story = (
            "**Panel 1: The First Spark**\n**CAPTION:** The journey begins.\n**HERO:** \"Let's go!\"\n\n"
            "**Panel 2: Danger Ahead**\n**NARRATION:** Trouble looms.\n\n"
            "**Panel 3: The Clash**\n**CAPTION:** Sparks fly.\n\n"
            "**Panel 4: The Turning Point**\n**CAPTION:** The hero rallies.\n\n"
            "**Panel 5: Resolution**\n**CAPTION:** The city is saved."
        )
        outline = [
            {"panel": i, "title": f"Title {i}", "scene_description": f"Desc {i}", "image_prompt": f"Prompt {i}"}
            for i in range(1, 6)
        ]

        layout = build_comic_layout(image_paths, story, outline)
        self.assertEqual(len(layout), 5)
        for i, panel in enumerate(layout, start=1):
            self.assertEqual(panel["panel"], i)
            self.assertTrue(panel["title"])
            self.assertEqual(panel["image_path"], image_paths[i - 1])
            self.assertTrue(panel["text"])
            self.assertTrue(panel["scene_description"])

    def test_05_exporters_pdf(self):
        """Test save_pdf creates a multi-page PDF with DejaVu font."""
        # Generate an actual test image first
        img_path = generate_image("Hero running", filename="pdf_test_panel")
        layout = [
            {
                "panel": i,
                "title": f"Epic Chapter {i}",
                "image_path": img_path,
                "text": f"**CAPTION:** Caption for chapter {i}.\n**NARRATION:** Epic tale unfolds.\n**HERO:** \"Victory!\"",
                "scene_description": f"Vivid scene {i} featuring intense action."
            }
            for i in range(1, 6)
        ]

        pdf_path = save_pdf(layout)
        self.assertTrue(pdf_path.startswith("static/exports/"))
        self.assertTrue(pdf_path.endswith(".pdf"))
        abs_pdf = os.path.join(CURRENT_DIR, pdf_path)
        self.assertTrue(os.path.exists(abs_pdf), f"PDF file {abs_pdf} must exist")
        self.assertGreater(os.path.getsize(abs_pdf), 1000, "PDF file must have content")

    def test_06_fastapi_endpoints(self):
        """Test all FastAPI routes."""
        # 1. GET "/"
        res_index = self.client.get("/")
        self.assertEqual(res_index.status_code, 200)
        self.assertIn("ComicCraft", res_index.text)
        self.assertIn("form", res_index.text)

        # 2. GET "/test-image"
        res_img = self.client.get("/test-image?prompt=speeding_car")
        self.assertEqual(res_img.status_code, 200)
        data = res_img.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue("image_path" in data)

        # 3. POST "/generate-comic/json"
        res_json = self.client.post("/generate-comic/json", json={
            "prompt": "A time-traveling samurai visits modern Shibuya",
            "character_name": "Kenshin",
            "setting": "Modern Tokyo",
            "tone": "Action-Packed",
            "style": "Modern Graphic Novel"
        })
        self.assertEqual(res_json.status_code, 200)
        res_data = res_json.json()
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(len(res_data["layout"]), 5)
        self.assertTrue(res_data["pdf_path"].endswith(".pdf"))

        # 4. POST "/generate" (HTML form submission)
        res_form = self.client.post("/generate", data={
            "prompt": "Space explorer discovering ancient alien artifact",
            "character_name": "Astra",
            "setting": "Alien Nebula Space Station",
            "tone": "Sci-Fi Thriller & High Stakes",
            "style": "Modern Graphic Novel"
        })
        self.assertEqual(res_form.status_code, 200)
        self.assertIn("PANEL 1", res_form.text)
        self.assertIn("Download Your Comic as PDF", res_form.text)

        # 5. GET "/export-success"
        res_export = self.client.get(f"/export-success?pdf_path={res_data['pdf_path']}")
        self.assertEqual(res_export.status_code, 200)
        self.assertIn("COMIC BOOK READY!", res_export.text)
        self.assertIn("Go Create Another Comic", res_export.text)

if __name__ == "__main__":
    unittest.main()

# ComicCraft 💥 AI Comic Book Creator

ComicCraft is a full-stack AI web application that automatically writes, plans, illustrates, and binds personalized 5-panel comic books and exports them as downloadable PDFs.

---

## 🚀 Architecture Overview

```
comiccraft/
├── app/
│   ├── main.py             # FastAPI initialization & static file mounting
│   ├── routes.py           # Web and JSON API endpoints
│   ├── gemini_flash.py     # Gemini 1.5 Flash 5-panel JSON planner
│   ├── gemini_pro.py       # Gemini 1.5 Pro narrative & dialogue scriptwriter
│   ├── image_generator.py  # Diffusers StableDiffusionPipeline (runwayml/stable-diffusion-v1-5)
│   ├── layout_builder.py   # Sequencer that merges art, scripts, and descriptions
│   └── exporters.py        # Multi-page Unicode PDF generator using FPDF & DejaVu fonts
├── templates/
│   ├── index.html          # Interactive comic studio creator form
│   ├── comic_preview.html  # 5-panel comic view with speech bubbles & prompts
│   └── export_success.html # PDF download confirmation screen
├── static/
│   ├── panels/             # Rendered comic illustrations (.png)
│   ├── exports/            # Timestamped exported PDF books (.pdf)
│   └── fonts/              # DejaVu Unicode TrueType fonts (.ttf)
├── .env                    # Runtime configuration & API keys
├── requirements.txt        # Python dependency manifest
└── test_pipeline.py        # Comprehensive test suite
```

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Create or edit `.env` in the root folder:
```ini
# Gemini API Key (Get yours at https://aistudio.google.com/)
GEMINI_API_KEY=your_actual_gemini_api_key

# Image Generator Configuration
# Set to 'false' to use live Diffusers StableDiffusionPipeline with CUDA GPU
USE_MOCK_IMAGE_GEN=true

HOST=127.0.0.1
PORT=8000
```

> **Note**: If `GEMINI_API_KEY` is not provided or if running offline, ComicCraft gracefully uses its built-in fallback story planner and prompt visualizer so you can test the full pipeline immediately!

### 3. Run the Development Server
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser at `http://127.0.0.1:8000`.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | ComicCraft Studio home form |
| `POST` | `/generate` | Form submission endpoint; executes pipeline and displays comic preview |
| `POST` | `/generate-comic/json` | JSON API endpoint taking `PromptRequest` and returning panel layout & PDF path |
| `GET` | `/export-success?pdf_path=...` | Download confirmation screen |
| `GET` | `/test-image?prompt=...` | Direct image generator testing endpoint |

---

## 🧪 Running Automated Tests

Run the test suite:
```bash
python test_pipeline.py
```
This tests:
1. `generate_outline()` with 5-panel JSON schema validation
2. `generate_story()` comic narration formatting
3. `generate_image()` image creation and filesystem storage
4. `build_comic_layout()` zipping and text extraction
5. `save_pdf()` multi-page DejaVu Unicode PDF assembly
6. All FastAPI routes (`GET /`, `POST /generate`, `POST /generate-comic/json`, `GET /export-success`, `GET /test-image`)

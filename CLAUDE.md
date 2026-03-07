# AI VC

A macOS desktop app that pitches a question to five famous VC personas — Vinod Khosla, Doug Leone, Ben Horowitz, Peter Thiel, and Pat Grady — and gets their takes plus a cross-discussion.

## Stack
- **Backend**: FastAPI + uvicorn (`app.py`)
- **VC personas**: `vcs.py` — persona definitions, system prompts, model routing
- **Frontend**: Single-page HTML/JS (`static/index.html`) with Tailwind + marked.js via CDN
- **Desktop**: `main.py` starts the server in a background thread, opens in a native macOS WKWebView window via pywebview
- **Build**: `bash build.sh` → `dist/AI VC.app` (PyInstaller)

## Key files
- `app.py` — FastAPI routes, 2-round pipeline (takes → discussion)
- `vcs.py` — VC dataclass, system prompts, model routing (`call_vc`)
- `main.py` — app entry point
- `build.sh` — generates icon, runs PyInstaller

## API keys
Loaded from `~/ai-vc/.env` (symlinked to `~/ai-board/.env`). Required keys:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `XAI_API_KEY`

## VC → Model mapping
- Vinod Khosla (Khosla Ventures) → Claude
- Doug Leone (Sequoia) → GPT-4o
- Ben Horowitz (a16z) → Gemini
- Peter Thiel (Founders Fund) → Grok
- Pat Grady (Sequoia) → Claude

## Pipeline
1. **Round 1**: All 5 VCs answer in parallel with their persona system prompt
2. **Round 2**: Each VC reads all 5 Round 1 takes and responds as themselves (cross-discussion)
No consolidated synthesis — just individual takes and discussion.

## Build & run
```bash
# Run in dev
cd ~/ai-vc && python3 -m uvicorn app:app --reload

# Build .app
bash build.sh
# Output: dist/AI VC.app
```

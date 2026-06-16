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
Loaded from `~/Developer/ai-vc/.env` (symlinked to `~/Developer/ai-board/.env`). Required keys:
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
cd ~/Developer/ai-vc && python3 -m uvicorn app:app --reload

# Build .app
bash build.sh
# Output: dist/AI VC.app
```

---

# Coding Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

> Source: https://github.com/forrestchang/andrej-karpathy-skills

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

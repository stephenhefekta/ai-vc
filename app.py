import asyncio
import io
import json
import os
from pathlib import Path
from typing import List, Optional, Tuple

from dotenv import load_dotenv
load_dotenv(Path.home() / 'Developer' / 'ai-vc' / '.env')

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from vcs import Attachment, VCS, VC_DISPLAY, call_vc

app = FastAPI(title="AI VC")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── History (persisted to disk, survives app restarts) ───────────────
HISTORY_FILE = Path.home() / 'Developer' / 'ai-vc' / 'history.json'
MAX_SESSIONS = 100

def _read_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception:
            pass
    return []

def _write_history(sessions):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(sessions))

@app.get("/api/history")
async def get_history():
    return JSONResponse(_read_history())

@app.post("/api/history")
async def save_session(request: Request):
    session = await request.json()
    sessions = _read_history()
    sessions.insert(0, session)
    if len(sessions) > MAX_SESSIONS:
        sessions = sessions[:MAX_SESSIONS]
    _write_history(sessions)
    return JSONResponse({"ok": True})

@app.delete("/api/history/{session_id}")
async def delete_session(session_id: str):
    sessions = [s for s in _read_history() if s.get("id") != session_id]
    _write_history(sessions)
    return JSONResponse({"ok": True})


async def _process_upload(file: UploadFile) -> Attachment:
    """Read uploaded file, extracting text from PDFs."""
    data = await file.read()
    mime = (file.content_type or "application/octet-stream").split(";")[0].strip()
    name = file.filename or "file"

    is_pdf = mime == "application/pdf" or name.lower().endswith(".pdf")
    if is_pdf:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            text = "\n\n".join(p.extract_text() or "" for p in reader.pages)
            data = text.encode("utf-8")
            mime = "text/plain"
        except Exception as e:
            data = f"[PDF extraction failed: {e}]".encode()
            mime = "text/plain"

    return Attachment(filename=name, mime_type=mime, data=data)


async def _call(
    vc_key: str, prompt: str, atts: List[Attachment] = []
) -> Tuple[str, Optional[str], Optional[str]]:
    try:
        answer = await call_vc(VCS[vc_key], prompt, atts)
        return vc_key, answer, None
    except Exception as e:
        return vc_key, None, str(e)


@app.get("/")
async def root():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())


@app.post("/api/ask")
async def ask(
    question: str = Form(...),
    files: List[UploadFile] = File(default=[]),
):
    async def stream():
        q = question.strip()
        if not q:
            yield f"event: error\ndata: {json.dumps({'message': 'Question cannot be empty'})}\n\n"
            return

        def emit(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        # Process attachments
        atts: List[Attachment] = []
        for file in files:
            if file and file.filename:
                att = await _process_upload(file)
                atts.append(att)
                yield emit("file_info", {
                    "filename": att.filename,
                    "kind": "image" if att.is_image else "text",
                })

        # ── Round 1: Initial takes ───────────────────────────────────────────
        yield emit("phase", {"phase": "initial", "message": "Getting initial takes from all five VCs…"})

        tasks = [asyncio.create_task(_call(k, q, atts)) for k in VCS]
        answers: dict = {}
        for coro in asyncio.as_completed(tasks):
            key, answer, error = await coro
            result = answer if answer else f"[Error: {error}]"
            answers[key] = result
            yield emit("vc_take", {"vc": key, "answer": result})

        # ── Round 2: Cross-discussion ────────────────────────────────────────
        yield emit("phase", {"phase": "discussion", "message": "VCs are now responding to each other…"})

        takes_block = "\n\n".join(
            f"**{VC_DISPLAY[k]['name']} ({VC_DISPLAY[k]['firm']})**: {v}"
            for k, v in answers.items()
        )

        def make_discussion_prompt(vc_key: str) -> str:
            vc = VCS[vc_key]
            own = f"{vc.name} ({vc.firm})"
            return (
                f'The following question was put to five VC partners:\n\n'
                f'"{q}"\n\n'
                f"Here are all five initial takes (yours is labeled **{own}**):\n\n"
                f"{takes_block}\n\n"
                "Now respond as yourself. React to the other VCs' takes — where do you agree, "
                "where do you push back, and what important angle do you think is being missed? "
                "Be specific and direct."
            )

        # Pass image attachments to round 2 so VCs can still reference them
        critique_atts = [a for a in atts if a.is_image]

        discussion_tasks = [
            asyncio.create_task(_call(k, make_discussion_prompt(k), critique_atts))
            for k in VCS
        ]
        for coro in asyncio.as_completed(discussion_tasks):
            key, response, error = await coro
            result = response if response else f"[Error: {error}]"
            yield emit("vc_response", {"vc": key, "response": result})

        yield emit("done", {})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

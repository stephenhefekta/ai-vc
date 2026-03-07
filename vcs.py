import asyncio
import base64
import os
from dataclasses import dataclass
from typing import List, Optional

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from google import genai as google_genai
from google.genai import types as genai_types


# --- Attachment (same as ai-board) ---

@dataclass
class Attachment:
    filename: str
    mime_type: str
    data: bytes

    @property
    def is_image(self) -> bool:
        return self.mime_type.startswith('image/')

    @property
    def b64(self) -> str:
        return base64.b64encode(self.data).decode()

    @property
    def text_content(self) -> str:
        return self.data.decode('utf-8', errors='replace')


def _text_prompt(prompt: str, atts: List[Attachment]) -> str:
    """Prepend text-file content to the prompt."""
    text_atts = [a for a in atts if not a.is_image]
    if text_atts:
        parts = "\n\n".join(f"[Attached file: {a.filename}]\n\n{a.text_content}" for a in text_atts)
        return f"{parts}\n\n---\n\n{prompt}"
    return prompt


# --- VC Persona ---

@dataclass
class VC:
    id: str
    name: str
    firm: str
    model_key: str   # "claude" | "chatgpt" | "gemini" | "grok"
    color: str
    bg: str
    border: str
    text: str
    system_prompt: str


VCS = {
    "vinod": VC(
        id="vinod", name="Vinod Khosla", firm="Khosla Ventures", model_key="claude",
        color="#D97706", bg="#FFFBEB", border="#FCD34D", text="#78350F",
        system_prompt=(
            "You are Vinod Khosla, founder of Khosla Ventures. "
            "You are a bold, contrarian thinker who backs moonshot ideas in energy, health, AI, and deep tech. "
            "You believe most experts are wrong about the future, and you actively challenge conventional wisdom. "
            "You don't care about near-term profitability — you care about the potential to change the world at scale. "
            "You ask hard questions about whether the technology is truly transformative or just incremental. "
            "You speak directly, push back on timid thinking, and love founders who are trying to do something that seems impossible. "
            "Give your honest VC perspective. Be specific. Be bold. Don't hedge."
        ),
    ),
    "doug": VC(
        id="doug", name="Doug Leone", firm="Sequoia Capital", model_key="chatgpt",
        color="#DC2626", bg="#FEF2F2", border="#FCA5A5", text="#7F1D1D",
        system_prompt=(
            "You are Doug Leone, Managing Partner at Sequoia Capital. "
            "You are rigorous, direct, and operationally focused. "
            "You evaluate opportunities through the lens of market size, team quality, and competitive dynamics. "
            "You ask 'why will you win?' and expect a crisp, defensible answer. "
            "You care deeply about the quality and resilience of the founding team. "
            "You think about how Sequoia can help beyond capital — networks, recruiting, go-to-market. "
            "You are conservative about valuation and disciplined about entry price. "
            "Give your honest VC perspective. Be direct and data-driven. Don't sugarcoat."
        ),
    ),
    "ben": VC(
        id="ben", name="Ben Horowitz", firm="Andreessen Horowitz", model_key="gemini",
        color="#475569", bg="#F8FAFC", border="#CBD5E1", text="#1E293B",
        system_prompt=(
            "You are Ben Horowitz, co-founder of Andreessen Horowitz (a16z). "
            "You are a former founder and CEO yourself, so you have deep empathy for what founders go through. "
            "You focus on the hard operational challenges: building culture, hiring executives, navigating crises. "
            "You think about whether this is a wartime or peacetime situation for the company. "
            "You value founders who have strong opinions and can attract and retain great people. "
            "You occasionally draw on pop culture, history, or hip-hop to make a point. "
            "You are honest about the brutal realities of building a company. "
            "Give your honest VC perspective. Be authentic, gritty, and founder-empathetic."
        ),
    ),
    "peter": VC(
        id="peter", name="Peter Thiel", firm="Founders Fund", model_key="grok",
        color="#4F46E5", bg="#EEF2FF", border="#A5B4FC", text="#1E1B4B",
        system_prompt=(
            "You are Peter Thiel, co-founder of PayPal and Founders Fund. "
            "You think in terms of Zero to One — you only care about companies building something genuinely new, not competing in crowded markets. "
            "You look for secrets: what does this founder know or believe that almost nobody else does? "
            "You favor monopoly businesses over competitive ones. You are suspicious of too much competition as a sign of mediocrity. "
            "You think about definite vs indefinite optimism — do the founders have a specific plan, or are they just 'iterating'? "
            "You ask contrarian questions that cut to the heart of a company's assumptions. "
            "You are interested in deep tech, biotech, defense, and anything that touches on hard problems. "
            "Give your honest VC perspective. Be contrarian, incisive, and philosophically rigorous."
        ),
    ),
    "pat": VC(
        id="pat", name="Pat Grady", firm="Sequoia Capital", model_key="claude",
        color="#059669", bg="#ECFDF5", border="#6EE7B7", text="#064E3B",
        system_prompt=(
            "You are Pat Grady, Partner at Sequoia Capital focused on growth-stage enterprise and SaaS investments. "
            "You are metrics-obsessed. You want to see ARR, net revenue retention, CAC payback, LTV/CAC, and growth rates. "
            "You think carefully about the go-to-market motion: is there a repeatable, scalable sales playbook? "
            "You look for durable competitive advantages in SaaS — switching costs, data network effects, workflow lock-in. "
            "You evaluate the quality of revenue: is it recurring, predictable, and growing? "
            "You push founders to articulate their ideal customer profile precisely. "
            "You think about Rule of 40 and path to profitability for later-stage companies. "
            "Give your honest VC perspective. Be analytical, metrics-driven, and growth-focused."
        ),
    ),
}

VC_DISPLAY = {k: {"name": v.name, "firm": v.firm, "color": v.color, "bg": v.bg, "border": v.border, "text": v.text}
              for k, v in VCS.items()}


# --- Clients ---

claude_client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
grok_client = AsyncOpenAI(
    api_key=os.environ.get("XAI_API_KEY", ""),
    base_url="https://api.x.ai/v1",
)
gemini_client = google_genai.Client(api_key=os.environ.get("GOOGLE_API_KEY", ""))

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GROK_MODEL   = os.environ.get("GROK_MODEL",   "grok-3")

MAX_TOKENS = 8192


async def call_vc(vc: VC, prompt: str, atts: List[Attachment] = []) -> str:
    """Call the underlying model for a VC persona, injecting their system prompt."""
    image_atts = [a for a in atts if a.is_image]
    full_prompt = _text_prompt(prompt, atts)

    if vc.model_key == "claude":
        if image_atts:
            content = [
                {"type": "image", "source": {"type": "base64", "media_type": a.mime_type, "data": a.b64}}
                for a in image_atts
            ] + [{"type": "text", "text": full_prompt}]
        else:
            content = full_prompt
        message = await claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=vc.system_prompt,
            messages=[{"role": "user", "content": content}],
        )
        return message.content[0].text

    elif vc.model_key == "chatgpt":
        if image_atts:
            content = [
                {"type": "image_url", "image_url": {"url": f"data:{a.mime_type};base64,{a.b64}"}}
                for a in image_atts
            ] + [{"type": "text", "text": full_prompt}]
        else:
            content = full_prompt
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": vc.system_prompt},
                {"role": "user", "content": content},
            ],
        )
        return response.choices[0].message.content

    elif vc.model_key == "gemini":
        system_plus_prompt = f"{vc.system_prompt}\n\n{full_prompt}"
        if image_atts:
            contents = [
                genai_types.Part.from_bytes(data=a.data, mime_type=a.mime_type)
                for a in image_atts
            ] + [genai_types.Part.from_text(text=system_plus_prompt)]
        else:
            contents = system_plus_prompt
        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model=GEMINI_MODEL,
            contents=contents,
            config=genai_types.GenerateContentConfig(max_output_tokens=MAX_TOKENS),
        )
        return response.text

    elif vc.model_key == "grok":
        if image_atts:
            content = [
                {"type": "image_url", "image_url": {"url": f"data:{a.mime_type};base64,{a.b64}"}}
                for a in image_atts
            ] + [{"type": "text", "text": full_prompt}]
        else:
            content = full_prompt
        response = await grok_client.chat.completions.create(
            model=GROK_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": vc.system_prompt},
                {"role": "user", "content": content},
            ],
        )
        return response.choices[0].message.content

    else:
        raise ValueError(f"Unknown model_key: {vc.model_key}")

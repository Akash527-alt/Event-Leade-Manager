

import httpx

from .config import settings
from .models import Lead

REQUEST_TIMEOUT_SECONDS = 30


class AINotConfigured(Exception):
    """GEMINI_API_URL / GEMINI_API_KEY have not been filled in."""


class AIServiceError(Exception):
    """The Gemini API failed or returned something unusable."""


_TONE_GUIDE = {
    "friendly": "warm, friendly and conversational",
    "professional": "polished, professional and respectful",
    "concise": "very short and direct (under 90 words)",
}


def _lead_context(lead: Lead) -> str:
    return (
        f"Name: {lead.name}\n"
        f"Company: {lead.company}\n"
        f"Email: {lead.email}\n"
        f"Met at event: {lead.event}\n"
        f"Current follow-up status: {lead.status.replace('_', ' ')}\n"
        f"Notes from our conversation:\n{lead.notes or '(no notes)'}"
    )


def build_summary_prompt(lead: Lead) -> str:
    return (
        "You are an assistant for a B2B sales team that meets people at events.\n"
        "Summarise the interaction notes below for a busy teammate. Use 2-4 short "
        "bullet points covering: what they care about, any commitments or next "
        "steps, and anything time-sensitive. Use only facts present in the notes; "
        "do not invent details.\n\n"
        f"{_lead_context(lead)}"
    )


def build_follow_up_prompt(lead: Lead, tone: str, sender_name: str) -> str:
    sign_off = sender_name or "[Your name]"
    return (
        "You are an assistant for a B2B sales team that meets people at events.\n"
        f"Write a follow-up email to the person below. Tone: {_TONE_GUIDE[tone]}.\n"
        "Rules: start with a line 'Subject: ...', then a blank line, then the body. "
        "Reference the event and something specific from the notes. Include one clear "
        "next step. Do not invent facts that are not in the notes. "
        f"Sign off as {sign_off}.\n\n"
        f"{_lead_context(lead)}"
    )


def generate_text(prompt: str) -> str:
    """Send a prompt to Gemini and return the generated text."""
    if not settings.ai_configured:
        raise AINotConfigured(
            "AI is not configured yet. Set GEMINI_API_URL and GEMINI_API_KEY in backend/.env."
        )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 600},
    }
    headers = {"x-goog-api-key": settings.gemini_api_key, "Content-Type": "application/json"}

    try:
        response = httpx.post(
            settings.gemini_api_url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        raise AIServiceError(f"Gemini API returned HTTP {exc.response.status_code}.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise AIServiceError("Could not reach the Gemini API.") from exc

    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AIServiceError("Gemini returned no usable answer (it may have been blocked).") from exc

    if not text:
        raise AIServiceError("Gemini returned an empty answer.")
    return text


def summarize_notes(lead: Lead) -> str:
    return generate_text(build_summary_prompt(lead))


def draft_follow_up(lead: Lead, tone: str, sender_name: str) -> str:
    return generate_text(build_follow_up_prompt(lead, tone, sender_name))

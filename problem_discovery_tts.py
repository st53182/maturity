"""OpenAI Text-to-Speech for problem-discovery replies (same API key as chat)."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_MAX_CHARS = 4096  # OpenAI TTS input limit

_DEFAULT_MODEL = "tts-1"
_DEFAULT_VOICE = "nova"
_DEFAULT_SPEED = 0.95


def _voice_for_locale(locale: str) -> str:
    loc = (locale or "en").strip().lower().split("-", 1)[0]
    if loc == "ru":
        return (os.getenv("OPENAI_TTS_VOICE_RU") or os.getenv("OPENAI_TTS_VOICE") or _DEFAULT_VOICE).strip().lower()
    return (os.getenv("OPENAI_TTS_VOICE_EN") or os.getenv("OPENAI_TTS_VOICE") or _DEFAULT_VOICE).strip().lower()


def openai_tts_available() -> bool:
    if os.getenv("OPENAI_TTS_DISABLE", "").strip().lower() in ("1", "true", "yes"):
        return False
    return bool((os.getenv("OPENAI_API_KEY") or "").strip())


def synthesize_openai_mp3(text: str, locale: str) -> bytes:
    """Return MP3 bytes via OpenAI audio.speech. Raises on API errors."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty text")
    if len(raw) > _MAX_CHARS:
        raw = raw[:_MAX_CHARS]

    from openai import OpenAI

    timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "120"))
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=timeout)
    model = (os.getenv("OPENAI_TTS_MODEL") or _DEFAULT_MODEL).strip()
    voice = _voice_for_locale(locale)
    try:
        speed = float(os.getenv("OPENAI_TTS_SPEED", str(_DEFAULT_SPEED)))
    except ValueError:
        speed = _DEFAULT_SPEED
    speed = max(0.25, min(4.0, speed))

    # instructions: supported on newer models; omit if API rejects
    kwargs = {
        "model": model,
        "voice": voice,
        "input": raw,
        "response_format": "mp3",
        "speed": speed,
    }
    resp = client.audio.speech.create(**kwargs)
    data = resp.read() if hasattr(resp, "read") else resp.content
    if not data:
        raise RuntimeError("empty audio from OpenAI TTS")
    return data

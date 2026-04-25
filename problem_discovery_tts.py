"""Google Cloud Text-to-Speech (Neural2) for problem-discovery replies."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Neural2 voices — see https://cloud.google.com/text-to-speech/docs/voices
_DEFAULT_RU = "ru-RU-Neural2-A"
_DEFAULT_EN = "en-US-Neural2-J"

_MAX_CHARS = 4500


def gcp_tts_configured() -> bool:
    if os.getenv("GCP_TTS_DISABLE", "").strip().lower() in ("1", "true", "yes"):
        return False
    cred = (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    if cred:
        p = Path(cred).expanduser()
        return p.is_file()
    # On GCP (Cloud Run, GCE) ADC may work without a file; allow explicit opt-in.
    return os.getenv("GCP_TTS_USE_ADC", "").strip().lower() in ("1", "true", "yes")


def synthesize_neural2_mp3(text: str, locale: str) -> bytes:
    """Return MP3 bytes. Raises on API/auth errors."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty text")
    if len(raw) > _MAX_CHARS:
        raw = raw[:_MAX_CHARS]

    try:
        from google.cloud import texttospeech
    except ImportError as e:
        raise RuntimeError("google-cloud-texttospeech is not installed") from e

    loc = (locale or "en").strip().lower().split("-", 1)[0]
    if loc == "ru":
        lang = "ru-RU"
        name = (os.getenv("GCP_TTS_VOICE_RU") or _DEFAULT_RU).strip()
    else:
        lang = "en-US"
        name = (os.getenv("GCP_TTS_VOICE_EN") or _DEFAULT_EN).strip()

    try:
        speaking_rate = float(os.getenv("GCP_TTS_SPEAKING_RATE", "0.95"))
    except ValueError:
        speaking_rate = 0.95
    speaking_rate = max(0.25, min(4.0, speaking_rate))

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=raw)
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang,
        name=name,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate,
    )
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )
    content = response.audio_content
    if not content:
        raise RuntimeError("empty audio from TTS")
    return content

"""
FastAPI HTTP server for text-to-speech voice generation.

Run with: uvicorn server:app --host 0.0.0.0 --port 8000
"""

import io
import logging

import scipy.io.wavfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from pocket_tts import TTSModel

# Configure logging.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Max allowed text length to avoid memory/timeout issues.
MAX_TEXT_LENGTH = 5000

# Predefined voices supported by pocket_tts (without voice cloning).
PREDEFINED_VOICES = [
    "alba", "marius", "javert", "jean", "fantine",
    "cosette", "eponine", "azelma",
]

# TTS model loaded once at startup.
tts_model = None


# Request body schema for /voice/generate.
class VoiceGenerateRequest(BaseModel):
    """Request body for POST /voice/generate."""

    text: str = Field(..., description="Text to convert to speech")
    voice: str = Field(default="alba", description="Voice name (default: alba)")


# Create FastAPI app.
app = FastAPI(
    title="TTS Voice Generation Server",
    description="Generate speech from text using predefined voices.",
)


@app.on_event("startup")
async def load_model():
    """Load TTS model once when server starts."""
    global tts_model
    logger.info("Loading TTS model...")
    tts_model = TTSModel.load_model()
    logger.info("TTS model ready.")


@app.post("/voice/generate", response_class=Response)
async def voice_generate(request: VoiceGenerateRequest):
    """
    Generate speech from text and return WAV audio.

    Request body: { "text": "...", "voice": "alba" }
    Response: audio/wav
    """
    # Validate text: required and non-empty after trimming.
    text = request.text.strip() if request.text else ""
    if not text:
        raise HTTPException(
            status_code=400,
            detail="text cannot be empty",
        )

    # Validate text length.
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"text exceeds max length of {MAX_TEXT_LENGTH} characters",
        )

    # Validate voice: non-empty and must be predefined.
    voice = request.voice.strip() if request.voice else ""
    if not voice:
        raise HTTPException(
            status_code=400,
            detail="voice cannot be empty",
        )
    if voice not in PREDEFINED_VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid voice '{voice}'. Available: {', '.join(PREDEFINED_VOICES)}",
        )

    try:
        # Get voice state for the requested voice.
        voice_state = tts_model.get_state_for_audio_prompt(voice)
        # Generate audio from text.
        audio = tts_model.generate_audio(voice_state, text)
        # Convert to WAV bytes.
        buffer = io.BytesIO()
        scipy.io.wavfile.write(
            buffer,
            tts_model.sample_rate,
            audio.numpy(),
        )
        wav_bytes = buffer.getvalue()
    except Exception as e:
        logger.exception("Voice generation failed")
        raise HTTPException(
            status_code=500,
            detail="Voice generation failed",
        ) from e

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": 'attachment; filename="speech.wav"',
        },
    )

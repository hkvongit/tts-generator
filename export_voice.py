"""
Convert a WAV audio file to a .safetensors voice file for Pocket TTS.

Use this to pre-process a voice sample so the server can load it quickly
without re-encoding the audio each time.

Usage:
    python export_voice.py
    python export_voice.py --input path/to/voice.wav --output path/to/voice.safetensors
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import scipy.io.wavfile

from pocket_tts import TTSModel, export_model_state


def _load_hf_token_from_env() -> None:
    """Load HuggingFace token from .env so voice-cloning model can be fetched."""
    if os.environ.get("HF_TOKEN"):
        return
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key in ("HF_TOKEN", "HUGGING_FACE_AUTH_TOKEN", "HUGGING_FACE_HUB_TOKEN") and value:
                os.environ.setdefault("HF_TOKEN", value)
                return

# Logging setup.
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Default paths from the voice cloning plan.
DEFAULT_INPUT = Path("voices/sources/akhila.wav")
DEFAULT_OUTPUT = Path("voices/safetensors/akhila.safetensors")

# Pocket TTS recommends 3–10 seconds of audio for best voice cloning.
MIN_RECOMMENDED_DURATION_SEC = 3
MAX_TRUNCATE_SEC = 30


def get_audio_duration_seconds(path: Path) -> float:
    """Read WAV file and return duration in seconds."""
    sample_rate, data = scipy.io.wavfile.read(str(path))
    num_samples = data.shape[0] if data.ndim == 1 else data.shape[0] * data.shape[1]
    return num_samples / sample_rate


def main() -> int:
    """Run the export: WAV -> voice state -> safetensors."""
    parser = argparse.ArgumentParser(
        description="Convert WAV audio to .safetensors voice file for Pocket TTS."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input WAV file path (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output .safetensors file path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Reduce logging output",
    )
    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    input_path = args.input.resolve()
    output_path = args.output.resolve()

    # Edge case: WAV file not found.
    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        return 1

    # Edge case: Audio too short (warning only).
    try:
        duration_sec = get_audio_duration_seconds(input_path)
        if duration_sec < MIN_RECOMMENDED_DURATION_SEC:
            logger.warning(
                "Audio is %.1f seconds. Pocket TTS recommends 3–10 seconds for best results.",
                duration_sec,
            )
    except Exception as e:
        logger.warning("Could not read audio duration: %s", e)

    # Create output directory if it does not exist.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure HuggingFace token is available (from .env or huggingface-cli login).
    _load_hf_token_from_env()

    # Load TTS model and convert audio to voice state.
    try:
        logger.info("Loading TTS model (this may take a moment on first run)...")
        tts_model = TTSModel.load_model()

        logger.info("Encoding audio prompt...")
        voice_state = tts_model.get_state_for_audio_prompt(
            input_path,
            truncate=True,
        )

        logger.info("Saving to %s", output_path)
        export_model_state(voice_state, output_path)

    except ValueError as e:
        err_msg = str(e)
        if "voice cloning" in err_msg.lower():
            # Edge case: Voice-cloning model not available (HuggingFace terms / login).
            logger.error(
                "Voice cloning is not available. Do ALL of these:\n"
                "  1. Open https://huggingface.co/kyutai/pocket-tts in a browser\n"
                "  2. Log in, then click 'Agree and access repository'\n"
                "  3. Put your token in .env as: HF_TOKEN=hf_xxxx\n"
                "     Or run: huggingface-cli login\n"
                "  4. Run this script again"
            )
        else:
            logger.error("Export failed: %s", e)
        return 1
    except Exception as e:
        # Edge case: Corrupt/invalid audio or other errors.
        logger.exception("Export failed: %s", e)
        return 1

    logger.info("Done. Use this path in your server: %s", output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

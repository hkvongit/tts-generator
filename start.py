"""
Generate speech from a markdown file using Pocket TTS.

Supports predefined voices (alba, marius, etc.) and custom voices from voices/safetensors.

Usage:
    python start.py
    python start.py --input article.md --voice akhila --output speech.wav
"""

import argparse
import re
from pathlib import Path

import scipy.io.wavfile

from pocket_tts import TTSModel

# Custom cloned voices (safetensors path relative to project root).
# Matches server.py.
CUSTOM_VOICES = {
    "coldfusion": Path(__file__).resolve().parent / "voices/safetensors/coldfusion-voice.safetensors",
    "my-voice": Path(__file__).resolve().parent / "voices/safetensors/my-voice.safetensors",
    "akhila": Path(__file__).resolve().parent / "voices/safetensors/akhila.safetensors",
}

# Predefined voices from Pocket TTS.
PREDEFINED_VOICES = [
    "alba", "marius", "javert", "jean", "fantine",
    "cosette", "eponine", "azelma",
]

AVAILABLE_VOICES = list(PREDEFINED_VOICES) + list(CUSTOM_VOICES)

DEFAULT_INPUT = Path(__file__).resolve().parent / "input.md"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output.wav"


def read_text_from_md(path: Path) -> str:
    """
    Read a markdown file and return plain text for TTS.

    Strips markdown syntax (headers, bold, links) so the spoken output
    sounds natural.
    """
    raw = path.read_text(encoding="utf-8")
    # Remove markdown headers (# ## ###).
    text = re.sub(r"^#+\s*", "", raw, flags=re.MULTILINE)
    # Remove bold/italic: **text** and *text* -> text.
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    # Links: [text](url) -> text.
    text = re.sub(r"\[(.+?)\]\([^)]+\)", r"\1", text)
    # Collapse multiple newlines to space, then trim.
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = text.strip()
    return text


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate speech from a markdown file using Pocket TTS."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input markdown file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output WAV file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--voice",
        "-v",
        type=str,
        default="alba",
        choices=AVAILABLE_VOICES,
        help=f"Voice name. Predefined: {', '.join(PREDEFINED_VOICES)}. Custom: {', '.join(CUSTOM_VOICES)}",
    )
    args = parser.parse_args()

    input_path = args.input.resolve()
    output_path = args.output.resolve()

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    text = read_text_from_md(input_path)
    if not text.strip():
        print("Error: No text content in the markdown file.")
        return 1

    print(f"Loading TTS model...")
    tts_model = TTSModel.load_model()

    # Resolve voice: custom safetensors path or predefined name.
    voice_source = CUSTOM_VOICES.get(args.voice, args.voice)
    print(f"Using voice: {args.voice}")
    voice_state = tts_model.get_state_for_audio_prompt(voice_source)

    print(f"Generating audio ({len(text)} chars)...")
    audio = tts_model.generate_audio(voice_state, text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    scipy.io.wavfile.write(str(output_path), tts_model.sample_rate, audio.numpy())
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

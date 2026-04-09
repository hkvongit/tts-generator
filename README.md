# TTS Server

Text-to-speech server using Pocket TTS (Kyutai). Supports predefined voices and custom voice cloning.

---

## .env
Create a .env file in the root of project
```
HF_TOKEN=hugginface_token
# Get the huggingface_token from https://huggingface.co/settings/tokens and allow access to the required repositories (kyutai/pocket-tts, first get access to this model from https://huggingface.co/kyutai/pocket-tts).
```

## start.py

**What it does:** Generates speech from a markdown file using Pocket TTS. Loads the model, picks a voice, strips markdown syntax for natural speech, and saves the result as a WAV file.

**When to use:** Quick tests, debugging, or generating audio from articles or notes stored in markdown.

**Voices:** Predefined (alba, marius, javert, jean, fantine, cosette, eponine, azelma) or custom from `voices/safetensors` (coldfusion, my-voice, akhila).

**Usage:**
```bash
source venv/bin/activate
# Default: reads input.md, writes output.wav, voice alba
python start.py

# Custom input, voice, and output
python start.py --input article-01.md --voice akhila --output speech.wav

# Short form
python start.py -i my-article.md -v coldfusion -o out.wav
```

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--input` | `-i` | `input.md` | Markdown file to read text from |
| `--output` | `-o` | `output.wav` | Output WAV file path |
| `--voice` | `-v` | `alba` | Voice name (predefined or custom) |

Markdown syntax (headers, bold, links) is stripped so the spoken output sounds natural.

---

## export_voice.py

**What it does:** Converts a WAV voice sample into a `.safetensors` file. Pocket TTS can then load this file directly instead of re-encoding the WAV every time, which speeds up voice loading.

**When to use:** After adding a new custom voice (your own recording or any WAV sample). Run once per voice; the server can reuse the safetensors file.

**Usage:**
```bash
source venv/bin/activate
python3 -m export_voice
# Or with custom paths:
python3 -m export_voice.py --input voices/sources/my-voice.wav --output voices/safetensors/my-voice.safetensors
# --input and --output are optional
```

**Requirements:** Voice cloning needs a HuggingFace token. Put `HF_TOKEN=hf_xxxx` in a `.env` file, or run `huggingface-cli login`. Use 3–10 seconds of clear speech in the source WAV for better results.

---

## HTTP Server (server.py)

**What it does:** FastAPI server with `POST /voice/generate` that returns WAV audio from JSON input.

**How to run:**
```bash
cd /Users/harikrishnanv/Documents/personal-projects/RSS-Feeder/TTS-server
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000
```

**Example request:**
```bash
curl -X POST http://localhost:8000/voice/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?", "voice": "alba"}' \
  --output speech.wav
```
# Implementation Plan: Simple HTTP Voice Generation Server

## Requirement Summary

A simple HTTP server with:
- **Method:** POST
- **URL:** `/voice/generate`
- **Request body:** JSON `{ "text": "...", "voice": "alba" }`
- **Response:** Audio output (WAV file)

---

## Technical Approach

### 1. Server Framework
**FastAPI** — pocket_tts already uses FastAPI internally, so this keeps dependencies consistent.

### 2. Flow
1. Load TTS model once at startup (same as `start.py`).
2. API server lives in a **separate file** (`server.py`) — distinct from the standalone `start.py` script.
3. On each request:
   - Parse JSON body → get `text` and `voice`
   - Get voice state via `tts_model.get_state_for_audio_prompt(voice)`
   - Generate audio via `tts_model.generate_audio(voice_state, text)`
   - Return WAV bytes with correct headers

### 3. Response Format
- **Content-Type:** `audio/wav`
- **Body:** Raw WAV binary (from `scipy.io.wavfile.write` to buffer, or use `io.BytesIO`)

---

## Edge Cases & Handling

### Input validation

| Edge Case | Behavior | Suggested Handling |
|-----------|----------|-------------------|
| Missing `text` | Request fails | Return 400 with message: "text is required" |
| Empty string `"text": ""` | Nothing to speak | Return 400 with message: "text cannot be empty" |
| `text` is only whitespace | Same as empty | Trim and return 400 if empty after trim |
| Missing `voice` | Need default | Option A: Use default "alba" — Option B: Return 400 |
| Empty string `"voice": ""` | Invalid voice | Return 400: "voice cannot be empty" |
| Unknown voice (e.g. `"xyz"`) | Model will fail | Return 400: "Invalid voice 'xyz'. Available: alba, marius, javert, jean, fantine, cosette, eponine, azelma" |
| Very long text | Memory / timeout | Add a max length (e.g. 5000 chars) and return 400 if exceeded |
| Non-JSON body | Parse error | Return 400: "Invalid JSON" |
| Wrong content-type (not application/json) | May fail to parse | Return 415 or still try to parse JSON |

### Voice support

| Voice Type | Example | Supported? |
|------------|---------|------------|
| Predefined names | "alba", "marius", "javert", etc. | Yes |
| Local file path | "./my_voice.wav" | Depends on pocket_tts config (voice cloning) |
| Hugging Face URL | "hf://kyutai/tts-voices/..." | May need voice cloning weights |

**Recommendation:** Support only predefined voices initially:
`alba`, `marius`, `javert`, `jean`, `fantine`, `cosette`, `eponine`, `azelma`

(Matches your current setup without voice cloning.)

### Server behavior

| Edge Case | Handling |
|-----------|----------|
| Model load fails at startup | Exit with clear error; do not start server |
| Generation fails mid-request | Catch exception, return 500 with generic message |
| Concurrent requests | FastAPI handles; model may be CPU-bound — consider request queue or rate limit if needed |
| Server startup time | Model load is slow (~10–30s); log "Loading model..." and "Ready" |

---

## Proposed API Contract

### Request
```http
POST /voice/generate
Content-Type: application/json

{
  "text": "Hello, how are you?",
  "voice": "alba"
}
```

### Success Response (200)
```http
Content-Type: audio/wav
Content-Disposition: attachment; filename="speech.wav"

<binary WAV data>
```

### Error Responses
- **400** — Bad request: missing/invalid `text`, invalid `voice`, or invalid JSON
- **500** — Server error: generation failed

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `server.py` | **Create** — FastAPI HTTP server (separate file) with `/voice/generate` endpoint |
| `requirements.txt` | **Create** (optional) — fastapi, uvicorn, pocket-tts, scipy |
| `start.py` | **No change** — keep as standalone script |

---

## Open Decisions

1. **Default voice:** When `voice` is missing, use `"alba"` or require it and return 400?
2. **Voice scope:** Support only predefined voices, or also local paths / Hugging Face URLs?
3. **Max text length:** Use a limit (e.g. 5000 chars) or leave unlimited?
4. **Port:** Default port for the server (e.g. 8000)?

---

## Implementation Checklist (After Approval)

- [ ] Create `server.py` with FastAPI app
- [ ] Load model once at startup
- [ ] Implement `POST /voice/generate` with JSON body
- [ ] Validate `text` and `voice`
- [ ] Generate WAV and return as response
- [ ] Add error handling (400, 500)
- [ ] Create `requirements.txt` if needed
- [ ] Document how to run (e.g. `uvicorn server:app --host 0.0.0.0 --port 8000`)

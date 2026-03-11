## Requirement:
This code is working perfectly. Can we write a separate file for a simple HTTP server in which we can request for a voice output.

API Method: POST
URL: /voice/generate
Request body (application/json):
{
  "text": "Hai, how are you",
  "voice": "alba",
}

Response = audio output

**Deliverable:** A separate file `server.py` containing a FastAPI HTTP server.

---

## API Flow (Sequence Diagram)

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant TTSModel

    Client->>+Server: POST /voice/generate
    Note over Client,Server: { "text": "...", "voice": "alba" }

    Server->>Server: Validate text & voice
    Server->>TTSModel: get_state_for_audio_prompt(voice)
    TTSModel-->>Server: voice_state

    Server->>TTSModel: generate_audio(voice_state, text)
    TTSModel-->>Server: audio (PCM tensor)

    Server->>Server: Convert to WAV bytes
    Server-->>-Client: 200 OK, audio/wav
```

---

## Request Processing Flow

```mermaid
flowchart TD
    A[POST /voice/generate] --> B{Valid JSON?}
    B -->|No| C[Return 400]
    B -->|Yes| D{text valid?}
    D -->|Empty/missing| C
    D -->|Yes| E{voice valid?}
    E -->|Invalid/missing| C
    E -->|Yes| F[Get voice state from model]
    F --> G[Generate audio]
    G --> H{Success?}
    H -->|No| I[Return 500]
    H -->|Yes| J[Convert to WAV]
    J --> K[Return 200 + audio]
```

---

## System Architecture

```mermaid
flowchart LR
    subgraph Client
        A[HTTP Client]
    end

    subgraph Server
        B[FastAPI Server]
        C[TTS Model]
        B --> C
    end

    A -->|POST JSON| B
    B -->|WAV audio| A
```
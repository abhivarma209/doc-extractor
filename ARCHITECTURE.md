# Architecture — Document Extractor

## System Overview

```
Client (Swagger / HTTP)
        |
        v
FastAPI Application
        |
        +---> POST /extract       (JSON body — raw text)
        |
        +---> POST /extract/file  (multipart — PDF or txt)
                    |
                    v
            file_handler.py
            - Content type validation (415)
            - File size check — 10MB limit (413)
            - PDF extraction via pypdf
            - UTF-8 decode for text files
            - Empty extraction guard (422)
                    |
                    v
            extractor.py
            - Token counting via tiktoken
            - Graceful truncation at 3000 tokens
            - Instructor + OpenAI API call
            - Pydantic schema validation + auto-retry
            - truncated flag set post-call
                    |
                    v
            ExtractionResponse (Pydantic)
            - Validated structured JSON
            - Returned to client
```

## Key Design Decisions

### 1. Two endpoints instead of one
`POST /extract` accepts raw text for programmatic use.
`POST /extract/file` accepts file uploads for human use.
Kept separate because they have different request formats — JSON body vs multipart form data. You cannot mix a JSON body with a file upload in the same request.

### 2. Instructor over manual JSON parsing
Instructor injects the Pydantic schema as a JSON schema tool definition, then auto-retries if the model returns invalid output. Alternative was parsing `response.choices[0].message.content` manually and handling `json.JSONDecodeError` ourselves. Instructor handles this more robustly.

### 3. Temperature = 0
Extraction tasks require deterministic output. Temperature 0 ensures the same document always produces the same extraction. Any value above 0 introduces randomness that corrupts structured data.

### 4. Truncation over rejection
Documents over 3000 tokens are truncated rather than rejected with an error. A truncated extraction is more useful than no extraction. The `truncated: bool` field in the response tells the caller that results may be partial.

### 5. Specific exception handling
Five specific exception types are caught separately:
- `RateLimitError` → 429 (try again)
- `AuthenticationError` → 500 (config issue)
- `APIConnectionError` → 503 (network issue)
- `ValidationError` → 422 (model output issue)
- `Exception` → 500 (unknown, always logged)

Generic `except:` was avoided because it swallows error information and makes debugging impossible.

### 6. Grounding instructions in system prompt
Two critical instructions prevent hallucination:
- "If a field is not present, return null" — prevents invented values
- "Never invent or infer data not explicitly stated" — grounds model to source document

Without these, the model fabricates plausible-sounding but incorrect data for missing fields.

### 7. HTTPException passthrough in file endpoint
```
except HTTPException:
    raise  # pass through 415, 413, 422 from file_handler unchanged
```
Without this line, specific error codes from `file_handler.py` get caught by the generic `except Exception` handler and returned as 500, losing all diagnostic information.

## File Structure

```
doc-extractor/
├── main.py           # FastAPI app, endpoints, middleware, error handling
├── extractor.py      # LLM logic — token counting, API call, truncation
├── file_handler.py   # File processing — validation, PDF extraction, decoding
├── models.py         # Pydantic models — request/response schemas
├── requirements.txt  # Python dependencies
├── Dockerfile        # Multi-stage build
├── docker-compose.yml
├── .env.example      # Environment variable template
├── ARCHITECTURE.md   # This file
└── docs/
    └── LEARNINGS.md  # Concepts learned building this project
```

## Token Economics

Every API call has hidden structural overhead (~16 tokens) beyond your actual content.
At `gpt-4o-mini` pricing, the entire Month 1 of development costs under $2.

Context accumulation in multi-turn chat: each turn resends full history.
Turn 1 = 23 tokens. Turn 10 = potentially hundreds just in history overhead.
Solutions: summarisation, sliding window, selective memory injection.

## Production Checklist

- [x] Secrets via environment variables, never in code or image
- [x] .env in .gitignore and .dockerignore
- [x] Specific exception handling per error type
- [x] Structured logging with latency per request
- [x] CORS middleware configured
- [x] Health check endpoint
- [x] Multi-stage Dockerfile for smaller image
- [x] Empty document/extraction validation before LLM call
- [x] truncated flag so callers know extraction may be partial

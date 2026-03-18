# Smart Document Extractor

A production-grade document extraction API built with FastAPI, OpenAI, and Instructor.

## What it does
Accepts any text document and a question, returns structured JSON data 
extracted from the document using GPT-4o-mini with Pydantic validation.

## Tech stack
- **FastAPI** — async Python API
- **Instructor** — structured LLM outputs with Pydantic validation
- **tiktoken** — token counting and graceful truncation
- **Docker** — containerised for consistent deploys

## Run locally
```bash
cp .env.example .env        # add your OPENAI_API_KEY
docker compose up --build
```

## API
`POST /extract` — extract structured data from a document  
`GET /health`   — health check  
`GET /docs`     — Swagger UI

## Architecture decisions
- Temperature=0 for deterministic extraction
- Graceful truncation at 3000 tokens with truncated flag in response
- Specific exception handling per OpenAI error type
- Structured logging with latency and confidence per request
```

Also create `.env.example` — a template that shows what env vars are needed without exposing real values:
```
OPENAI_API_KEY=sk-your-key-here
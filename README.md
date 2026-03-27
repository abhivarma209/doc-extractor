# Document Extractor API

A production-grade document extraction API that accepts PDF or text files and returns structured JSON data using GPT-4o-mini.

## Live Demo
**API:** https://doc-extractor-production.up.railway.app  
**Docs:** https://doc-extractor-production.up.railway.app/docs

## What it does

Upload any invoice, report, or document — ask a question — get back validated structured data.

```
POST /extract/file
{
  "invoice_number": "INV-2025-0042",
  "vendor_name": "CloudStack Solutions Pvt Ltd",
  "items": [
    { "description": "Azure AKS", "quantity": 1, "unit_price": 12000, "total": 12000 }
  ],
  "total_amount": 30798.89,
  "confidence": "high",
  "truncated": false
}
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/extract` | Extract from raw text (JSON body) |
| POST | `/extract/file` | Extract from PDF or .txt file upload |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

## Tech Stack

- **FastAPI** — async Python API framework
- **Instructor** — structured LLM outputs with Pydantic validation and auto-retry
- **pypdf** — PDF text extraction
- **tiktoken** — token counting and graceful truncation
- **Docker** — containerised for consistent deploys
- **Railway** — cloud deployment

## Run Locally

```bash
git clone https://github.com/abhivarma209/doc-extractor
cd doc-extractor
cp .env.example .env        # add your OPENAI_API_KEY
docker compose up --build
# API live at http://localhost:8000/docs
```

## Architecture Decisions

See [ARCHITECTURE.md](./docs/ARCHITECTURE.md) for detailed design decisions.

## Learnings

See [docs/LEARNINGS.md](./docs/LEARNINGS.md) for concepts covered building this project.
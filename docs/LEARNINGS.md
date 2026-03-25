# Learnings — Document Extractor

Concepts covered while building this project from scratch.

---

## 1. How LLMs Actually Work

### The core mental model
An LLM is sophisticated autocomplete — it predicts the next token from all previous tokens, one at a time. Everything else (reasoning, extraction, coding) is emergent from doing this on enormous amounts of human text.

### Tokens
- A token is roughly 0.75 words
- Common English words = 1 token
- Rare words, names, technical terms = multiple tokens
- Code tokenizes at ~3-4 chars/token vs English at ~4-5 chars/token
- Spelling mistakes split into more tokens — clean writing is cheaper
- The name "Abhivarma" = 4 tokens (uncommon, gets split)

### Context window
The maximum tokens the model can see at once — input + output combined.
GPT-4o-mini: 128k token context window.
This is the most important constraint to design around as an AI engineer.

### Memory — the most misunderstood thing
**The model has NO memory between calls.**
Every API call is completely stateless. Multi-turn chat works by resending the entire conversation history on every single call. The context is rebuilt from scratch each time.

### Temperature
- 0 = deterministic, always same output
- 1 = creative, varied output
- Rule: precision tasks (extraction, classification) → temperature 0

---

## 2. Why RAG Exists — Complete Answer

Three distinct reasons:

1. **Context limits** — documents too large to fit in a single prompt
2. **Precision** — sending only relevant chunks makes the model more accurate. Too much irrelevant context degrades performance ("lost in the middle" problem)
3. **Knowledge freshness** — RAG injects private, proprietary, or real-time data the model was never trained on

---

## 3. Token Costs in Practice

Running a basic "capital of France" query costs 30 tokens:

```
System message overhead         :  3 tokens
"You are a helpful assistant."  :  4 tokens
User message overhead           :  3 tokens
"What is the capital of France?":  7 tokens
Reply primer                    :  3 tokens
Assistant overhead              :  3 tokens
─────────────────────────────────────────────
Prompt total                    : 23 tokens

"The capital of France is Paris." : 7 tokens
─────────────────────────────────────────────
Total                           : 30 tokens
```

**Context accumulation:** Every turn of a conversation resends full history.
Turn 1 = 23 tokens. Turn 10 = hundreds of tokens just in overhead.
Fix with: summarisation, sliding window, or selective memory injection.

---

## 4. The Three Message Roles

| Role | Purpose |
|------|---------|
| `system` | Sets behaviour and persona. Charged on every call. |
| `user` | Human input — document, question, instruction. |
| `assistant` | Previous model responses — used to reconstruct conversation history. |

---

## 5. Streaming

- Non-streaming: waits for full response, delivers at once
- Streaming: delivers tokens as generated — users see text appear in real time
- `stream=True` in API call, then iterate over chunks
- Each chunk contains only the NEW tokens
- `flush=True` in print() ensures tokens render immediately

```
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta is not None:
        print(delta, end="", flush=True)
```

---

## 6. Instructor Library

Instructor does two things:
1. Converts your Pydantic model to a JSON schema and injects it as a tool definition
2. If the model returns invalid output, auto-retries with the validation error fed back

You pass `response_model=YourPydanticClass` and get back a validated object directly.
No manual JSON parsing. No `response.choices[0].message.content`.

---

## 7. Prompt Engineering Patterns

### Grounding instructions — prevent hallucination
```
"If a field is not present in the document, return null."
"Never invent or infer data that is not explicitly stated."
```

### Clear separators in user prompt
```
user_prompt = (
    f"DOCUMENT:
{text}

"
    f"QUESTION:
{question}"
)
```
Always label sections clearly. Never run document and question together without a separator.

---

## 8. Docker Patterns

### Why python:3.11-slim
Full image = ~1GB. Slim = ~130MB. Smaller attack surface, faster deploys.

### Layer caching — critical optimisation
```dockerfile
# CORRECT — requirements cached separately from code
COPY requirements.txt .
RUN pip install -r requirements.txt   # cached unless requirements change
COPY . .                               # only this layer rebuilds on code changes

# WRONG — pip reinstalls on every code change
COPY . .
RUN pip install -r requirements.txt
```

### 0.0.0.0 vs 127.0.0.1
- `127.0.0.1` = localhost only, nothing outside container can reach it
- `0.0.0.0` = accept connections from anywhere — required in containers

### apt-get pattern
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends     gcc     && rm -rf /var/lib/apt/lists/*
```
All in one RUN command so the package index deletion happens in the same layer.

---

## 9. Git Hygiene

### Always in .gitignore
```
.env          # API keys — CRITICAL
__pycache__
*.pyc
.idea/
venv/
```

### If you staged files before .gitignore was complete
```bash
git rm -r --cached .   # clears index, keeps actual files
git add .              # re-adds with current .gitignore respected
```

### Never in Docker images
- .env files
- API keys as ENV in Dockerfile
- Local venv directories

---

## 10. FastAPI Patterns

### File uploads use multipart, not JSON
Cannot mix JSON body and file upload in the same request.
File upload endpoints use `Form(...)` for all non-file fields.

```
@app.post("/extract/file")
async def endpoint(
    file: UploadFile = File(...),
    question: str = Form(...)   # not Body(...)
):
```

### Never call endpoint functions from other endpoints
Call shared business logic functions directly.
Endpoint → business logic function (not endpoint → endpoint).

### HTTPException passthrough pattern
```
except HTTPException:
    raise  # never swallow specific HTTP errors into generic 500
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

### await async functions
`async def` functions must be awaited at the call site.
Forgetting `await` returns a coroutine object, not the actual result.

---

## 11. HTTP Status Codes — Use Specific Codes

| Code | Meaning | Use when |
|------|---------|----------|
| 400 | Bad Request | Generic client error (avoid — be specific) |
| 413 | Request Entity Too Large | File exceeds size limit |
| 415 | Unsupported Media Type | Wrong file type |
| 422 | Unprocessable Entity | Valid format, failed validation |
| 429 | Too Many Requests | Rate limit hit |
| 503 | Service Unavailable | Upstream dependency down |

---

## 12. Production Observability

Every request should log:
- Outcome (success/failure)
- Confidence level
- Whether truncation occurred
- Latency in seconds
- Filename for file uploads

```
logger.info(
    f"extraction successful | "
    f"confidence={response.confidence} | "
    f"truncated={response.truncated} | "
    f"duration={duration}s"
)
```

Without this, debugging production issues is guesswork.

# ── Stage 1: builder ──────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# install into a specific folder so we can copy it cleanly
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runner ───────────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

# copy only the installed packages from builder — not gcc, not cache
COPY --from=builder /install /usr/local

# copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
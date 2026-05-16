# ─────────────────────────────────────────────────────────────────
#  ARIA — Dockerfile  (lives inside backend/)
#  Deploy target : Hugging Face Spaces (Docker SDK)
#  Env name      : Aria-backend
#  Port          : 7860  ← HF Spaces required port
# ─────────────────────────────────────────────────────────────────

# ── Stage 1: base ─────────────────────────────────────────────────
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/Aria-backend \
    PATH="/app/Aria-backend/bin:$PATH" \
    PORT=7860

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: install dependencies ─────────────────────────────────
FROM base AS deps

# Create virtualenv named Aria-backend
RUN python -m venv /app/Aria-backend

# Dockerfile is inside backend/ → paths are relative to backend/
COPY requirements.txt ./

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── Stage 3: production image ──────────────────────────────────────
FROM base AS production

COPY --from=deps /app/Aria-backend /app/Aria-backend

# Copy all backend source (Dockerfile context = backend/)
COPY . .

# ── Hugging Face Spaces runs as root (non-root breaks HF file perms)
# so we skip adduser here — HF sandbox handles isolation

# HF Spaces REQUIRES port 7860
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:7860/api/health || exit 1

# Bind to 0.0.0.0:7860 for HF routing
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
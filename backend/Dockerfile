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

# curl only — no build-essential (saves ~350 MB).
# Pure-Python packages + pre-built wheels need no compiler.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: install dependencies ─────────────────────────────────
FROM base AS deps

RUN python -m venv /app/Aria-backend

# Dockerfile context = backend/ so no path prefix needed.
COPY requirements.txt ./

RUN pip install --upgrade pip --quiet \
 && pip install --no-cache-dir -r requirements.txt

# ── Stage 3: production image ──────────────────────────────────────
FROM base AS production

COPY --from=deps /app/Aria-backend /app/Aria-backend

# Copy backend source — requirements-test.txt, tests/, htmlcov/ are
# excluded by .dockerignore so they never reach the image.
COPY . .

# HF Spaces runs containers as root (non-root breaks HF file perms)
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:7860/api/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
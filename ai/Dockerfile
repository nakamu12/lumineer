FROM python:3.12-slim AS base
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ── deps stage: install only production dependencies ──────────────────────────
FROM base AS deps
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project

# ── dev stage ─────────────────────────────────────────────────────────────────
FROM base AS dev
COPY --from=deps /app/.venv ./.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8001
CMD ["uv", "run", "python", "main.py"]

# ── prod stage ────────────────────────────────────────────────────────────────
FROM base AS prod
COPY --from=deps /app/.venv ./.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
ENV APP_ENV=prod
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]

FROM python:3.12-slim AS base
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies
FROM base AS deps
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project

# Development
FROM base AS dev
COPY --from=deps /app/.venv ./.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8001
CMD ["uv", "run", "python", "main.py"]

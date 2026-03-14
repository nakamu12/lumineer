# =============================================================================
# Sample Dockerfile — Bun + Hono (Cloud Run deployment verification)
# Multi-stage build: install deps → copy source → run
# =============================================================================

# Stage 1: install dependencies
FROM oven/bun:1.2-alpine AS deps
WORKDIR /app
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile --production

# Stage 2: runtime image
FROM oven/bun:1.2-alpine AS runner
WORKDIR /app

# Cloud Run injects PORT env var (default 8080)
ENV PORT=8080
ENV NODE_ENV=production

COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
COPY src/ ./src/

# Non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

EXPOSE 8080

CMD ["bun", "run", "src/index.ts"]

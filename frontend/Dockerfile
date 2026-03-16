FROM oven/bun:1 AS base
WORKDIR /app

# Install dependencies
FROM base AS deps
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile

# Development
FROM base AS dev
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["bun", "run", "dev", "--host", "0.0.0.0"]

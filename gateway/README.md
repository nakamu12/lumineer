# Gateway

The **sole public entry point** for the Lumineer system. Built with Bun + Hono (TypeScript).

Responsibilities: CORS · request logging · IP-based rate limiting · reverse proxy to Backend.

**No business logic lives here.** If you find yourself adding domain rules to this service, they belong in `backend/` instead.

---

## Architecture position

```
Internet → Gateway (:3000) → Backend (:3001) → AI Processing (:8001)
                 ↑
         only publicly exposed
```

---

## Directory structure

```
gateway/src/
├── config/
│   └── settings.ts      # env var validation
├── middleware/
│   └── rate_limiter.ts  # IP-based rate limiting
├── routes/
│   └── proxy.ts         # /api/* → Backend proxy
└── index.ts             # app bootstrap
```

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3000` | Listening port |
| `BACKEND_URL` | `http://backend:3001` | Backend service URL |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated CORS origins |
| `RATE_LIMIT_WINDOW_MS` | `60000` | Rate limit window in ms |
| `RATE_LIMIT_MAX` | `100` | Max requests per window per IP |

---

## Development

```bash
# Install dependencies
bun install

# Start with hot-reload
BACKEND_URL=http://localhost:3001 bun dev

# Type check
bun run typecheck

# Lint
bun run lint

# Build
bun run build
```

---

## Proxy routing

| Path | Forwards to |
|------|-------------|
| `/health` | Returns `{"status":"ok"}` directly |
| `/api/*` | `BACKEND_URL/api/*` |

All other paths return `404`.

---

## Adding a new upstream service

Add one line to `routes/proxy.ts`:

```typescript
app.all("/new-service/*", proxyTo(settings.NEW_SERVICE_URL))
```

No changes needed to `backend/` or `ai/`. This is the key benefit of the Gateway pattern.

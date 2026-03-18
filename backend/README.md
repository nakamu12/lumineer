# Backend

The **Backend Service** for Lumineer. Built with Bun + Hono (TypeScript) following Clean Architecture.

Handles: JWT authentication · PostgreSQL persistence · AI Processing orchestration · REST API.

Internal only — accessible through the Gateway at `:3000/api/*`, not exposed directly to the internet in production.

---

## Architecture

```
interfaces/api/   → usecases/   → ports/   ← infrastructure/
                      ↕
                   domain/
              (entities, errors — no external deps)
```

| Layer | Location | Responsibility |
|-------|----------|---------------|
| Interfaces | `src/interfaces/api/` | Hono routes, request validation, response serialization |
| Use Cases | `src/domain/usecases/` | Business logic, orchestrates ports |
| Ports | `src/domain/ports/` | Abstract interfaces for external dependencies |
| Infrastructure | `src/infrastructure/` | Concrete implementations (DB, auth, AI client) |
| Config | `src/config/` | Settings validation, DI container |

---

## Directory structure

```
backend/src/
├── domain/
│   ├── entities/          # User, ChatSession, LearningPath, UserSettings
│   ├── ports/             # Repository interfaces, AI Processing port
│   ├── usecases/          # Core business logic
│   └── errors.ts          # Domain error types
├── infrastructure/
│   ├── auth/              # JWT issuer/verifier (jose), bcrypt password hashing
│   ├── db/                # Drizzle ORM schema, PostgreSQL repositories
│   └── llm/               # HTTP client to AI Processing service
├── interfaces/
│   └── api/
│       ├── middleware/    # JWT auth middleware
│       ├── routes/        # Route handlers (auth, search, chat, path, settings, course)
│       ├── schemas/       # Zod + OpenAPI schemas
│       └── types.ts       # Hono context variable types
├── config/
│   ├── container.ts       # Dependency injection container
│   └── settings.ts        # Environment variable validation
├── scripts/
│   └── seed.ts            # Database seeding
└── index.ts               # Server bootstrap
```

---

## Entities

| Entity | Description |
|--------|-------------|
| `User` | Registered user with hashed password |
| `ChatSession` | Named conversation thread |
| `ChatMessage` | Individual message (role: user / assistant) |
| `LearningPath` | Ordered list of courses with a goal |
| `UserSettings` | Per-user RAG pipeline configuration |

---

## API Endpoints

See [docs/API.md](../docs/API.md) for the full reference.

| Tag | Endpoints |
|-----|-----------|
| Auth | `POST /api/auth/register` · `/login` · `/refresh` · `GET /api/auth/me` |
| Courses | `POST /api/search` · `GET /api/courses/{id}` |
| AI Chat | `POST /api/chat` (SSE) |
| Chat Sessions | `GET/POST /api/chat/sessions` · `GET /api/chat/sessions/{id}/messages` |
| Learning Paths | `GET/POST /api/paths` |
| Settings | `GET/PUT /api/settings` |

Swagger UI: **http://localhost:3001/api/docs** (dev only)

---

## Environment variables

| Variable | Default | Required in prod |
|----------|---------|-----------------|
| `APP_ENV` | `dev` | — |
| `PORT` | `3001` | — |
| `DATABASE_URL` | `postgres://lumineer:lumineer@localhost:5432/lumineer` | ✓ |
| `AI_PROCESSING_URL` | `http://localhost:8001` | ✓ |
| `JWT_SECRET` | `dev-secret-...` | ✓ |
| `JWT_ACCESS_EXPIRES` | `15m` | — |
| `JWT_REFRESH_EXPIRES` | `7d` | — |

---

## Development

```bash
# Install dependencies
bun install

# Start with hot-reload (reads ../.env.local)
bun dev

# Run tests
bun test
bun test:watch

# Type check + lint
bun run typecheck
bun run lint

# Database
bun run db:generate    # generate migration files
bun run db:migrate     # apply migrations
bun run db:seed        # seed test data
```

---

## Database schema

Managed by [Drizzle ORM](https://orm.drizzle.team). Schema defined in `src/infrastructure/db/schema.ts`.

Tables: `users` · `chat_sessions` · `chat_messages` · `learning_paths` · `user_settings`

```bash
# After editing schema.ts, generate and apply a migration
bun run db:generate
bun run db:migrate
```

---

## Testing

Unit tests use **Vitest** with dependency injection — no database or network required.

```bash
bun test                    # run all tests
bun test:watch              # watch mode
bun test src/test/auth.test.ts  # single file
```

All use cases are tested by injecting mock implementations of the Port interfaces.

# Frontend

The **React SPA** for Lumineer. Built with Bun + Vite + Shadcn UI + Tailwind CSS.

---

## Pages

| Path | Auth | Component | Description |
|------|------|-----------|-------------|
| `/` | — | `HomePage` | Landing — value proposition, popular courses |
| `/explore` | — | `ExplorePage` | Course catalog — search bar, filters, AI summary panel, course cards |
| `/login` | — | `LoginPage` | Login / register |
| `/chat` | ✓ | `ChatPage` | AI conversation with course recommendations |
| `/path` | ✓ | `MyPathPage` | Learning path management |
| `/course/:id` | — | `CourseDetailPage` | Course detail view |
| `/settings` | ✓ | `SettingsPage` | Pipeline settings (reranker, format, top-k) |

---

## Directory structure

```
frontend/src/
├── app/
│   ├── App.tsx            # Root component, router provider
│   └── router.tsx         # React Router route definitions
├── features/              # Domain-driven feature modules
│   ├── auth/              # LoginPage, auth state
│   ├── chat/              # ChatPage, ChatMessage, ChatInput, SSE hooks
│   ├── course/            # CourseDetailPage, useCourseDetail
│   ├── explore/           # ExplorePage, CourseCard, SearchFilters, AiSummaryPanel
│   ├── home/              # HomePage
│   ├── path/              # MyPathPage
│   └── settings/          # SettingsPage
└── lib/
    ├── auth/              # ProtectedRoute, auth context
    ├── hooks/             # useApi, useDebounce (shared)
    ├── layout/            # PageLayout, Header
    ├── types/             # Shared TypeScript types
    └── ui/                # Shadcn UI primitives (Button, Card, Badge, etc.)
```

**Rule:** A component used in only one feature lives in `features/{name}/`. A component shared across two or more features lives in `lib/`.

---

## Key features

### Explore page — Google-style AI search

Type a query → course cards appear alongside an AI-generated summary panel. Natural language queries redirect to the Chat page.

### Chat page — SSE streaming

Messages stream token-by-token via Server-Sent Events. Course cards are rendered inline in assistant messages. Sessions are persisted to the backend (authenticated users only).

### Settings page — live pipeline control

Switch reranker strategy, context format, and top-k without redeployment. Changes take effect on the next API request.

---

## API communication

All requests go to the **Gateway** via Vite's dev proxy (dev) or the same origin (prod).

```typescript
// lib/hooks/useApi.ts
// Base URL defaults to "" (same origin) — Vite proxy handles /api/* → :3000
const API_BASE = import.meta.env.VITE_API_URL ?? ""
```

**Never call the Backend or AI Processing directly from the frontend.**

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `""` (same origin) | Gateway base URL |

In development, `vite.config.ts` proxies `/api/*` → `http://localhost:3000`.

---

## Development

```bash
# Install dependencies
bun install

# Start dev server with hot module replacement
bun dev             # http://localhost:5173

# Type check
bun run typecheck

# Lint
bun run lint

# Tests
bun test
bun test:watch

# Production build
bun run build
bun run preview     # preview production build locally
```

---

## UI Components

UI primitives come from [Shadcn UI](https://ui.shadcn.com) and live in `lib/ui/`. They are copied into the repo (not installed as a package) so they can be customized freely.

To add a new Shadcn component:

```bash
bunx shadcn@latest add <component-name>
```

Custom styling is done exclusively with Tailwind CSS utility classes. Do not add separate CSS files.

---

## Testing

Uses **Vitest** + **React Testing Library**.

```bash
bun test
bun test:watch
bun test src/features/auth/LoginPage.test.tsx  # single file
```

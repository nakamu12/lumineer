---
name: frontend-design
description: Lumineer のフロントエンドコンポーネント・ページを作成する。React + Shadcn UI + Tailwind CSS で Feature-based 構成に従い、洗練されたUIを実装する。
user_invocable: true
---

# /frontend-design — Lumineer Frontend Builder

Lumineer の React + Shadcn UI + Tailwind CSS フロントエンドで、洗練されたコンポーネント・ページを作成するスキル。

## Design Context

Lumineer は **Intelligent Course Discovery System** — AI でコースを探す体験を提供する。

**デザインコンセプト**: Clean & Scholarly — 学びの道を照らすミニマルで知的なデザイン。
- 余白を活かした低密度レイアウト
- 段階的開示（最初は最低限、展開で詳細）
- 一貫したカードデザイン・タイポグラフィ

## Architecture

```
frontend/src/
├── lib/              # Shared
│   ├── ui/           # Shadcn UI (auto-generated, don't manually edit)
│   ├── layout/       # Header, PageLayout
│   ├── hooks/        # useApi, useDebounce
│   └── types/        # Shared types
├── features/         # Domain features
│   ├── search/       # Course search
│   ├── recommend/    # Recommendations & learning paths
│   └── chat/         # Chat UI
└── app/              # Entry & routing
```

## Process

### Step 1: Identify Placement
- Feature-specific component → `features/{name}/components/`
- Shared across 2+ features → `lib/ui/` or `lib/layout/`
- API hook → `features/{name}/hooks/` or `lib/hooks/`
- Types → `features/{name}/types.ts` or `lib/types/`

### Step 2: Check Available Shadcn Components
```bash
ls frontend/src/lib/ui/
```

Add new ones if needed:
```bash
cd frontend && bunx shadcn@latest add {component}
```

### Step 3: Build the Component

Follow these patterns:
- Import Shadcn primitives from `@/lib/ui/*`
- Props with TypeScript interface
- Tailwind utility classes only (no CSS files)
- Responsive: `sm:`, `md:`, `lg:` breakpoints
- Theme tokens: `text-foreground`, `bg-background`, `text-muted-foreground`

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/lib/ui/card"
import { Badge } from "@/lib/ui/badge"

interface CourseCardProps {
  title: string
  organization: string
  level: string
  rating: number
  skills: string[]
}

export function CourseCard({ title, organization, level, rating, skills }: CourseCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        <p className="text-sm text-muted-foreground">{organization}</p>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="secondary">{level}</Badge>
          <span className="text-sm">⭐ {rating.toFixed(1)}</span>
        </div>
        <div className="flex flex-wrap gap-1">
          {skills.slice(0, 3).map((skill) => (
            <Badge key={skill} variant="outline" className="text-xs">{skill}</Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

### Step 4: Data Fetching
- API calls go through **Gateway** (`/api/*`) — never direct to AI Processing
- Use custom hooks: `features/{name}/hooks/useXxx.ts`
- Streaming (SSE) for chat/AI features

## Pages Reference

| Page | Path | Auth | Key Components |
|------|------|------|----------------|
| Home | `/` | No | Hero, QuickStart, PopularCourses |
| Explore | `/explore` | No | SearchBar, FilterPanel, CourseCardGrid, AISummary |
| Chat | `/chat` | Yes | MessageList, ChatInput, InlineCourseCard |
| My Path | `/path` | Yes | PathTimeline, ProgressTracker |
| Course Detail | `/course/:id` | No | CourseHeader, SkillTags, RelatedCourses |
| Settings | `/settings` | Yes | PipelineConfigForm |

## Rules
- All UI text in **English**
- No `any` — proper TypeScript types
- No direct AI Processing calls — always through API Layer
- Use Shadcn UI primitives — don't reinvent
- Import alias: `@/` → `src/`
- Check `@rules/15-styleguide.md` for design system details

## Commands
```bash
cd frontend && bun dev           # Dev server
cd frontend && bun run lint      # ESLint
cd frontend && bun run typecheck # tsc --noEmit
cd frontend && bun test          # Vitest
```

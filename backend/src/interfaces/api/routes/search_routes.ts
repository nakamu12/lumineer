import { createRoute } from "@hono/zod-openapi"
import type { OpenAPIHono } from "@hono/zod-openapi"
import { stream } from "hono/streaming"
import type { Container } from "../../../config/container.ts"
import { SearchRequestSchema, SearchResponseSchema, ChatRequestSchema } from "../schemas/search.ts"
import { ErrorResponseSchema } from "../schemas/common.ts"
import type { AppVariables } from "../types.ts"

const searchRoute = createRoute({
  method: "post",
  path: "/api/search",
  tags: ["Courses"],
  summary: "Search courses",
  description:
    "Search Coursera courses using natural language or keywords. Supports metadata filtering by level, organization, rating, and skills.",
  request: {
    body: {
      content: { "application/json": { schema: SearchRequestSchema } },
      required: true,
    },
  },
  responses: {
    200: {
      content: { "application/json": { schema: SearchResponseSchema } },
      description: "Search results with AI-generated summary",
    },
    400: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Invalid request body",
    },
    502: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "AI Processing Layer unavailable",
    },
  },
})

const chatAiRoute = createRoute({
  method: "post",
  path: "/api/chat",
  tags: ["AI Chat"],
  summary: "Chat with AI agent (SSE stream)",
  description:
    "Send a message to the Triage Agent via SSE streaming. Handles course search, skill gap analysis, and learning path generation.",
  request: {
    body: {
      content: { "application/json": { schema: ChatRequestSchema } },
      required: true,
    },
  },
  responses: {
    200: {
      description: "SSE stream of agent events",
    },
    502: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "AI Processing Layer unavailable",
    },
  },
})

type SSEEvent = {
  type: string
  content: string
}

function transformEvent(event: SSEEvent): string | null {
  switch (event.type) {
    case "text_delta":
      return `data: ${JSON.stringify({ type: "text", content: event.content })}\n\n`
    case "done":
      return `data: ${JSON.stringify({ type: "done" })}\n\n`
    case "error":
      return `data: ${JSON.stringify({ type: "error", content: event.content })}\n\n`
    case "handoff":
    case "tool_call":
    case "tool_result":
      return null
    default:
      return null
  }
}

export function registerSearchRoutes(
  app: OpenAPIHono<{ Variables: AppVariables }>,
  container: Container,
): void {
  app.openapi(searchRoute, async (c) => {
    const { query, level, organization, min_rating, skills, limit } = c.req.valid("json")
    const result = await container.searchCoursesUseCase.execute(query, {
      level,
      organization,
      min_rating,
      skills,
      limit,
    })
    return c.json(result, 200)
  })

  app.openapi(chatAiRoute, async (c) => {
    const { message, session_id } = c.req.valid("json")
    const userId = c.get("userId") as string | undefined

    c.header("Content-Type", "text/event-stream")
    c.header("Cache-Control", "no-cache")
    c.header("Connection", "keep-alive")
    c.header("X-Accel-Buffering", "no")

    return stream(c, async (s) => {
      let activeSessionId: string | null = null
      let assistantText = ""

      try {
        const { response: aiResponse, sessionId: resolvedSessionId } =
          await container.chatUseCase.getStream(message, session_id, userId)
        activeSessionId = resolvedSessionId

        if (resolvedSessionId) {
          await s.write(
            `data: ${JSON.stringify({ type: "session", session_id: resolvedSessionId })}\n\n`,
          )
        }

        const reader = aiResponse.body?.getReader()
        if (!reader) {
          await s.write(
            `data: ${JSON.stringify({ type: "error", content: "No response body" })}\n\n`,
          )
          return
        }

        const decoder = new TextDecoder()
        let buffer = ""

        while (true) {
          const { value, done } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split("\n")
          buffer = lines.pop() ?? ""

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue
            const raw = line.slice(6).trim()
            if (!raw) continue

            try {
              const event = JSON.parse(raw) as SSEEvent
              if (event.type === "text_delta") {
                assistantText += event.content
              }
              const transformed = transformEvent(event)
              if (transformed) {
                await s.write(transformed)
              }
            } catch {
              // skip malformed SSE lines
            }
          }
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "AI Processing unavailable"
        await s.write(`data: ${JSON.stringify({ type: "error", content: errorMessage })}\n\n`)
      } finally {
        if (activeSessionId && assistantText) {
          try {
            await container.chatUseCase.saveAssistantMessage(activeSessionId, assistantText)
          } catch {
            // best-effort persistence — do not fail the stream
          }
        }
      }
    })
  })
}

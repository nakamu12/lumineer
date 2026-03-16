import { createRoute } from "@hono/zod-openapi"
import type { OpenAPIHono } from "@hono/zod-openapi"
import type { Container } from "../../../config/container.ts"
import {
  SearchRequestSchema,
  SearchResponseSchema,
  ChatRequestSchema,
  ChatResponseSchema,
} from "../schemas/search.ts"
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
  summary: "Chat with AI agent",
  description:
    "Send a message to the Triage Agent. Handles course search, skill gap analysis, and learning path generation.",
  request: {
    body: {
      content: { "application/json": { schema: ChatRequestSchema } },
      required: true,
    },
  },
  responses: {
    200: {
      content: { "application/json": { schema: ChatResponseSchema } },
      description: "Agent response with optional course recommendations",
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
    const result = await container.chatUseCase.execute(message, session_id)
    return c.json(result, 200)
  })
}

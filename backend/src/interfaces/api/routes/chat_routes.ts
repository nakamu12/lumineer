import { createRoute, z } from "@hono/zod-openapi"
import type { OpenAPIHono } from "@hono/zod-openapi"
import type { Container } from "../../../config/container.ts"
import { NotFoundError } from "../../../domain/errors.ts"
import {
  ChatSessionSchema,
  ChatMessageSchema,
  CreateSessionRequestSchema,
} from "../schemas/chat.ts"
import { ErrorResponseSchema } from "../schemas/common.ts"
import type { AppVariables } from "../types.ts"

const listSessionsRoute = createRoute({
  method: "get",
  path: "/api/chat/sessions",
  tags: ["Chat Sessions"],
  summary: "List chat sessions",
  description: "Get all chat sessions for the authenticated user, ordered by most recent first.",
  responses: {
    200: {
      content: { "application/json": { schema: z.array(ChatSessionSchema) } },
      description: "List of chat sessions",
    },
    401: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Unauthorized",
    },
  },
})

const createSessionRoute = createRoute({
  method: "post",
  path: "/api/chat/sessions",
  tags: ["Chat Sessions"],
  summary: "Create a new chat session",
  request: {
    body: {
      content: { "application/json": { schema: CreateSessionRequestSchema } },
      required: false,
    },
  },
  responses: {
    201: {
      content: { "application/json": { schema: ChatSessionSchema } },
      description: "Chat session created",
    },
    401: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Unauthorized",
    },
  },
})

const listMessagesRoute = createRoute({
  method: "get",
  path: "/api/chat/sessions/{id}/messages",
  tags: ["Chat Sessions"],
  summary: "List messages in a chat session",
  description:
    "Get all messages for a specific chat session. Only accessible by the session owner.",
  request: {
    params: z.object({
      id: z.string().uuid().openapi({ example: "550e8400-e29b-41d4-a716-446655440000" }),
    }),
  },
  responses: {
    200: {
      content: { "application/json": { schema: z.array(ChatMessageSchema) } },
      description: "List of messages",
    },
    401: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Unauthorized",
    },
    404: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Chat session not found",
    },
  },
})

export function registerChatRoutes(
  app: OpenAPIHono<{ Variables: AppVariables }>,
  container: Container,
): void {
  app.openapi(listSessionsRoute, async (c) => {
    const userId = c.get("userId") as string | undefined
    if (!userId) {
      return c.json([], 200)
    }
    const sessions = await container.listChatSessionsUseCase.execute(userId)
    return c.json(
      sessions.map((s) => ({
        id: s.id,
        title: s.title,
        created_at: s.createdAt.toISOString(),
        updated_at: s.updatedAt.toISOString(),
      })),
      200,
    )
  })

  app.openapi(createSessionRoute, async (c) => {
    const userId = c.get("userId")
    const body = c.req.valid("json")
    const session = await container.createChatSessionUseCase.execute(userId, body?.title)
    return c.json(
      {
        id: session.id,
        title: session.title,
        created_at: session.createdAt.toISOString(),
        updated_at: session.updatedAt.toISOString(),
      },
      201,
    )
  })

  app.openapi(listMessagesRoute, async (c) => {
    const userId = c.get("userId")
    const { id } = c.req.valid("param")
    try {
      const messages = await container.listChatMessagesUseCase.execute(userId, id)
      return c.json(
        messages.map((m) => ({
          id: m.id,
          session_id: m.sessionId,
          role: m.role,
          content: m.content,
          created_at: m.createdAt.toISOString(),
        })),
        200,
      )
    } catch (err) {
      if (err instanceof NotFoundError) {
        return c.json({ error: err.message, status: 404 }, 404)
      }
      throw err
    }
  })
}

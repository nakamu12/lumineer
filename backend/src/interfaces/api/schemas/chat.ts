import { z } from "@hono/zod-openapi"

export const ChatSessionSchema = z
  .object({
    id: z.string().openapi({ example: "550e8400-e29b-41d4-a716-446655440000" }),
    title: z.string().openapi({ example: "New Chat" }),
    created_at: z.string().openapi({ example: "2026-03-16T10:00:00.000Z" }),
    updated_at: z.string().openapi({ example: "2026-03-16T10:00:00.000Z" }),
  })
  .openapi("ChatSession")

export const ChatMessageSchema = z
  .object({
    id: z.string().openapi({ example: "550e8400-e29b-41d4-a716-446655440001" }),
    session_id: z.string().openapi({ example: "550e8400-e29b-41d4-a716-446655440000" }),
    role: z.enum(["user", "assistant"]).openapi({ example: "user" }),
    content: z.string().openapi({ example: "I want to learn Python" }),
    created_at: z.string().openapi({ example: "2026-03-16T10:00:00.000Z" }),
  })
  .openapi("ChatMessage")

export const CreateSessionRequestSchema = z
  .object({
    title: z.string().min(1).max(200).optional().openapi({ example: "ML Study Plan" }),
  })
  .openapi("CreateSessionRequest")

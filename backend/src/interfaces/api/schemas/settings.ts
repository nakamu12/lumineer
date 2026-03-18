import { z } from "@hono/zod-openapi"

export const UserSettingsSchema = z
  .object({
    id: z.string().openapi({ example: "550e8400-e29b-41d4-a716-446655440000" }),
    reranker_strategy: z.enum(["none", "heuristic", "cross-encoder"]).openapi({ example: "none" }),
    context_format: z.enum(["json", "toon"]).openapi({ example: "json" }),
    top_k: z.number().int().openapi({ example: 10 }),
    similarity_threshold: z.number().openapi({ example: 0.7 }),
  })
  .openapi("UserSettings")

export const UpdateSettingsRequestSchema = z
  .object({
    reranker_strategy: z.enum(["none", "heuristic", "cross-encoder"]).optional(),
    context_format: z.enum(["json", "toon"]).optional(),
    top_k: z.union([z.literal(5), z.literal(10), z.literal(20)]).optional(),
    similarity_threshold: z.number().min(0.5).max(0.9).optional(),
  })
  .openapi("UpdateSettingsRequest")

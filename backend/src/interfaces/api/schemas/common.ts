import { z } from "@hono/zod-openapi"

export const ErrorResponseSchema = z
  .object({
    error: z.string(),
    status: z.number(),
  })
  .openapi("ErrorResponse")

export const HealthResponseSchema = z
  .object({
    status: z.literal("ok"),
    timestamp: z.string(),
  })
  .openapi("HealthResponse")

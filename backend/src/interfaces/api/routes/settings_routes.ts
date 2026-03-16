import { createRoute } from "@hono/zod-openapi"
import type { OpenAPIHono } from "@hono/zod-openapi"
import type { Container } from "../../../config/container.ts"
import { UserSettingsSchema, UpdateSettingsRequestSchema } from "../schemas/settings.ts"
import { ErrorResponseSchema } from "../schemas/common.ts"
import type { AppVariables } from "../types.ts"

const getSettingsRoute = createRoute({
  method: "get",
  path: "/api/settings",
  tags: ["Settings"],
  summary: "Get user settings",
  description:
    "Get pipeline settings for the authenticated user. Creates defaults if no settings exist.",
  responses: {
    200: {
      content: { "application/json": { schema: UserSettingsSchema } },
      description: "User settings",
    },
    401: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Unauthorized",
    },
  },
})

const updateSettingsRoute = createRoute({
  method: "put",
  path: "/api/settings",
  tags: ["Settings"],
  summary: "Update user settings",
  description:
    "Update pipeline settings. All fields are optional — only provided fields are updated.",
  request: {
    body: {
      content: { "application/json": { schema: UpdateSettingsRequestSchema } },
      required: true,
    },
  },
  responses: {
    200: {
      content: { "application/json": { schema: UserSettingsSchema } },
      description: "Updated settings",
    },
    401: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Unauthorized",
    },
  },
})

export function registerSettingsRoutes(
  app: OpenAPIHono<{ Variables: AppVariables }>,
  container: Container,
): void {
  app.openapi(getSettingsRoute, async (c) => {
    const userId = c.get("userId")
    const settings = await container.getUserSettingsUseCase.execute(userId)
    return c.json(
      {
        id: settings.id,
        reranker_strategy: settings.rerankerStrategy,
        context_format: settings.contextFormat,
        top_k: settings.topK,
        similarity_threshold: settings.similarityThreshold,
      },
      200,
    )
  })

  app.openapi(updateSettingsRoute, async (c) => {
    const userId = c.get("userId")
    const body = c.req.valid("json")
    const settings = await container.updateUserSettingsUseCase.execute(userId, {
      rerankerStrategy: body.reranker_strategy,
      contextFormat: body.context_format,
      topK: body.top_k,
      similarityThreshold: body.similarity_threshold,
    })
    return c.json(
      {
        id: settings.id,
        reranker_strategy: settings.rerankerStrategy,
        context_format: settings.contextFormat,
        top_k: settings.topK,
        similarity_threshold: settings.similarityThreshold,
      },
      200,
    )
  })
}

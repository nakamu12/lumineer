import { createRoute, z } from "@hono/zod-openapi"
import type { OpenAPIHono } from "@hono/zod-openapi"
import type { Container } from "../../../config/container.ts"
import { LearningPathSchema, CreatePathRequestSchema } from "../schemas/path.ts"
import { ErrorResponseSchema } from "../schemas/common.ts"
import type { AppVariables } from "../types.ts"

const listPathsRoute = createRoute({
  method: "get",
  path: "/api/paths",
  tags: ["Learning Paths"],
  summary: "List learning paths",
  description: "Get all learning paths for the authenticated user.",
  responses: {
    200: {
      content: { "application/json": { schema: z.array(LearningPathSchema) } },
      description: "List of learning paths",
    },
    401: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Unauthorized",
    },
  },
})

const createPathRoute = createRoute({
  method: "post",
  path: "/api/paths",
  tags: ["Learning Paths"],
  summary: "Create a learning path",
  request: {
    body: {
      content: { "application/json": { schema: CreatePathRequestSchema } },
      required: true,
    },
  },
  responses: {
    201: {
      content: { "application/json": { schema: LearningPathSchema } },
      description: "Learning path created",
    },
    401: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Unauthorized",
    },
  },
})

export function registerPathRoutes(
  app: OpenAPIHono<{ Variables: AppVariables }>,
  container: Container,
): void {
  app.openapi(listPathsRoute, async (c) => {
    const userId = c.get("userId")
    const paths = await container.listLearningPathsUseCase.execute(userId)
    return c.json(
      paths.map((p) => ({
        id: p.id,
        title: p.title,
        goal: p.goal,
        courses: p.courses,
        created_at: p.createdAt.toISOString(),
        updated_at: p.updatedAt.toISOString(),
      })),
      200,
    )
  })

  app.openapi(createPathRoute, async (c) => {
    const userId = c.get("userId")
    const { title, goal, courses } = c.req.valid("json")
    const path = await container.createLearningPathUseCase.execute(userId, {
      title,
      goal,
      courses,
    })
    return c.json(
      {
        id: path.id,
        title: path.title,
        goal: path.goal,
        courses: path.courses,
        created_at: path.createdAt.toISOString(),
        updated_at: path.updatedAt.toISOString(),
      },
      201,
    )
  })
}

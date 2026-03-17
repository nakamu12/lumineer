import { createRoute, z } from "@hono/zod-openapi"
import type { OpenAPIHono } from "@hono/zod-openapi"
import type { Container } from "../../../config/container.ts"
import { CourseSchema } from "../schemas/search.ts"
import { ErrorResponseSchema } from "../schemas/common.ts"
import type { AppVariables } from "../types.ts"

const getCourseRoute = createRoute({
  method: "get",
  path: "/api/courses/{id}",
  tags: ["Courses"],
  summary: "Get course by ID",
  description: "Retrieve a single course by its Qdrant point ID.",
  request: {
    params: z.object({
      id: z.string().openapi({ example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890" }),
    }),
  },
  responses: {
    200: {
      content: { "application/json": { schema: CourseSchema } },
      description: "Course details",
    },
    404: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Course not found",
    },
  },
})

export function registerCourseRoutes(
  app: OpenAPIHono<{ Variables: AppVariables }>,
  container: Container,
): void {
  app.openapi(getCourseRoute, async (c) => {
    const { id } = c.req.valid("param")
    const course = await container.getCourseDetailUseCase.execute(id)
    if (!course) {
      return c.json({ error: "Course not found", status: 404 }, 404)
    }
    return c.json(course, 200)
  })
}

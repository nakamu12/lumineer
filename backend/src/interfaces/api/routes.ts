import { OpenAPIHono, createRoute } from "@hono/zod-openapi"
import { swaggerUI } from "@hono/swagger-ui"
import type { Container } from "../../config/container.ts"
import { errorHandler } from "./middleware/error_handler.ts"
import { createAuthMiddleware } from "./middleware/auth.ts"
import { HealthResponseSchema } from "./schemas/common.ts"
import { registerAuthRoutes } from "./routes/auth_routes.ts"
import { registerSearchRoutes } from "./routes/search_routes.ts"
import { registerChatRoutes } from "./routes/chat_routes.ts"
import { registerPathRoutes } from "./routes/path_routes.ts"
import { registerSettingsRoutes } from "./routes/settings_routes.ts"
import type { AppVariables } from "./types.ts"

const healthRoute = createRoute({
  method: "get",
  path: "/health",
  tags: ["System"],
  summary: "Health check",
  responses: {
    200: {
      content: { "application/json": { schema: HealthResponseSchema } },
      description: "Service is healthy",
    },
  },
})

export function createRouter(container: Container): OpenAPIHono<{ Variables: AppVariables }> {
  const app = new OpenAPIHono<{ Variables: AppVariables }>()

  app.use("*", errorHandler)
  app.use("*", createAuthMiddleware(container.tokenIssuer))

  // OpenAPI spec
  app.doc("/openapi.json", {
    openapi: "3.0.0",
    info: {
      title: "Lumineer API",
      version: "0.1.0",
      description:
        "Intelligent Course Discovery System — AI-powered course search, skill gap analysis, and learning path generation.",
    },
    servers: [{ url: "http://localhost:3001", description: "Local development" }],
  })

  // Swagger UI
  app.get("/docs", swaggerUI({ url: "/openapi.json" }))

  // Health
  app.openapi(healthRoute, (c) =>
    c.json({ status: "ok" as const, timestamp: new Date().toISOString() }, 200),
  )

  // Domain routes
  registerAuthRoutes(app, container)
  registerSearchRoutes(app, container)
  registerChatRoutes(app, container)
  registerPathRoutes(app, container)
  registerSettingsRoutes(app, container)

  return app
}

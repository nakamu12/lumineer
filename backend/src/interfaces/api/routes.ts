import { OpenAPIHono, createRoute, z } from "@hono/zod-openapi"
import { swaggerUI } from "@hono/swagger-ui"
import type { Container } from "../../config/container.ts"
import { errorHandler } from "./middleware/error_handler.ts"
import { authMiddleware } from "./middleware/auth.ts"
import { verifyToken } from "../../infrastructure/auth/jwt.ts"

type AppVariables = { userId: string }

// ── Schemas ────────────────────────────────────────────────────────────────

const SearchRequestSchema = z
  .object({
    query: z.string().min(1).openapi({ example: "machine learning for beginners" }),
    level: z
      .enum(["Beginner", "Intermediate", "Advanced"])
      .optional()
      .openapi({ example: "Beginner" }),
    organization: z.string().optional().openapi({ example: "Stanford" }),
    min_rating: z.number().min(0).max(5).optional().openapi({ example: 4.5 }),
    skills: z
      .array(z.string())
      .optional()
      .openapi({ example: ["Python", "TensorFlow"] }),
    limit: z.number().int().min(1).max(50).optional().openapi({ example: 10 }),
  })
  .openapi("SearchRequest")

const CourseSchema = z
  .object({
    id: z.string(),
    title: z.string(),
    description: z.string(),
    level: z.enum(["Beginner", "Intermediate", "Advanced"]).nullable(),
    organization: z.string(),
    rating: z.number(),
    enrolled: z.number(),
    skills: z.array(z.string()),
    url: z.string(),
    instructor: z.string(),
    schedule: z.string(),
    modules: z.string(),
  })
  .openapi("Course")

const SearchResponseSchema = z
  .object({
    courses: z.array(CourseSchema),
    summary: z.string(),
    total: z.number(),
  })
  .openapi("SearchResponse")

const ChatRequestSchema = z
  .object({
    message: z.string().min(1).openapi({ example: "I want to become a data scientist" }),
    session_id: z.string().optional().openapi({ example: "sess_abc123" }),
  })
  .openapi("ChatRequest")

const ChatResponseSchema = z
  .object({
    message: z.string(),
    courses: z.array(CourseSchema).optional(),
    session_id: z.string(),
  })
  .openapi("ChatResponse")

const HealthResponseSchema = z
  .object({
    status: z.literal("ok"),
    timestamp: z.string(),
  })
  .openapi("HealthResponse")

const ErrorResponseSchema = z
  .object({
    error: z.string(),
    status: z.number(),
  })
  .openapi("ErrorResponse")

// ── Auth schemas ─────────────────────────────────────────────────────────────

const RegisterRequestSchema = z
  .object({
    email: z.string().email().openapi({ example: "user@example.com" }),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[0-9]/, "Password must contain at least one number")
      .openapi({ example: "Password1" }),
    display_name: z.string().min(1).max(100).openapi({ example: "Alice" }),
  })
  .openapi("RegisterRequest")

const LoginRequestSchema = z
  .object({
    email: z.string().email().openapi({ example: "user@example.com" }),
    password: z.string().min(1).openapi({ example: "password123" }),
  })
  .openapi("LoginRequest")

const RefreshRequestSchema = z
  .object({
    refresh_token: z.string().min(1).openapi({ example: "eyJhbGciOiJIUzI1NiJ9..." }),
  })
  .openapi("RefreshRequest")

const AuthResponseSchema = z
  .object({
    user: z.object({
      id: z.string(),
      email: z.string(),
      display_name: z.string(),
    }),
    access_token: z.string(),
    refresh_token: z.string(),
  })
  .openapi("AuthResponse")

const MeResponseSchema = z
  .object({
    id: z.string(),
    email: z.string(),
    display_name: z.string(),
    created_at: z.string(),
  })
  .openapi("MeResponse")

// ── Route definitions ──────────────────────────────────────────────────────

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

const chatRoute = createRoute({
  method: "post",
  path: "/api/chat",
  tags: ["Chat"],
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

const registerRoute = createRoute({
  method: "post",
  path: "/api/auth/register",
  tags: ["Auth"],
  summary: "Register a new user",
  request: {
    body: {
      content: { "application/json": { schema: RegisterRequestSchema } },
      required: true,
    },
  },
  responses: {
    201: {
      content: { "application/json": { schema: AuthResponseSchema } },
      description: "User registered successfully",
    },
    409: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Email already registered",
    },
  },
})

const loginRoute = createRoute({
  method: "post",
  path: "/api/auth/login",
  tags: ["Auth"],
  summary: "Login",
  request: {
    body: {
      content: { "application/json": { schema: LoginRequestSchema } },
      required: true,
    },
  },
  responses: {
    200: {
      content: { "application/json": { schema: AuthResponseSchema } },
      description: "Login successful",
    },
    401: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Invalid credentials",
    },
  },
})

const refreshRoute = createRoute({
  method: "post",
  path: "/api/auth/refresh",
  tags: ["Auth"],
  summary: "Refresh access token",
  request: {
    body: {
      content: { "application/json": { schema: RefreshRequestSchema } },
      required: true,
    },
  },
  responses: {
    200: {
      content: {
        "application/json": {
          schema: z.object({ access_token: z.string() }).openapi("RefreshResponse"),
        },
      },
      description: "New access token issued",
    },
    401: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Invalid refresh token",
    },
  },
})

const meRoute = createRoute({
  method: "get",
  path: "/api/auth/me",
  tags: ["Auth"],
  summary: "Get current user",
  responses: {
    200: {
      content: { "application/json": { schema: MeResponseSchema } },
      description: "Current user info",
    },
    401: {
      content: { "application/json": { schema: ErrorResponseSchema } },
      description: "Unauthorized",
    },
  },
})

// ── Router factory ─────────────────────────────────────────────────────────

export function createRouter(container: Container): OpenAPIHono<{ Variables: AppVariables }> {
  const app = new OpenAPIHono<{ Variables: AppVariables }>()

  app.use("*", errorHandler)
  app.use("*", authMiddleware)

  // OpenAPI spec
  app.doc("/openapi.json", {
    openapi: "3.0.0",
    info: {
      title: "Lumineer API",
      version: "0.1.0",
      description:
        "Intelligent Course Discovery System — AI-powered course search, skill gap analysis, and learning path generation.",
    },
    servers: [{ url: "http://localhost:8000", description: "Local development" }],
  })

  // Swagger UI
  app.get("/docs", swaggerUI({ url: "/openapi.json" }))

  // Health
  app.openapi(healthRoute, (c) =>
    c.json({ status: "ok" as const, timestamp: new Date().toISOString() }, 200),
  )

  // Course search
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

  // Chat
  app.openapi(chatRoute, async (c) => {
    const { message, session_id } = c.req.valid("json")
    const result = await container.chatUseCase.execute(message, session_id)
    return c.json(result, 200)
  })

  // Auth: register
  app.openapi(registerRoute, async (c) => {
    const { email, password, display_name } = c.req.valid("json")
    try {
      const { user, tokens } = await container.registerUserUseCase.execute({
        email,
        password,
        displayName: display_name,
      })
      return c.json(
        {
          user: { id: user.id, email: user.email, display_name: user.displayName },
          access_token: tokens.accessToken,
          refresh_token: tokens.refreshToken,
        },
        201,
      )
    } catch (err) {
      const message = err instanceof Error ? err.message : "Registration failed"
      if (message === "Email already registered") {
        return c.json({ error: message, status: 409 }, 409)
      }
      throw err
    }
  })

  // Auth: login
  app.openapi(loginRoute, async (c) => {
    const { email, password } = c.req.valid("json")
    try {
      const { user, tokens } = await container.loginUserUseCase.execute({
        email,
        password,
      })
      return c.json(
        {
          user: { id: user.id, email: user.email, display_name: user.displayName },
          access_token: tokens.accessToken,
          refresh_token: tokens.refreshToken,
        },
        200,
      )
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed"
      if (message === "Invalid email or password") {
        return c.json({ error: message, status: 401 }, 401)
      }
      throw err
    }
  })

  // Auth: refresh
  app.openapi(refreshRoute, async (c) => {
    const { refresh_token } = c.req.valid("json")
    try {
      const payload = await verifyToken(refresh_token)
      if (payload.type !== "refresh") {
        return c.json({ error: "Invalid token type", status: 401 }, 401)
      }
      const { signToken } = await import("../../infrastructure/auth/jwt.ts")
      const accessToken = await signToken(payload.sub, "access")
      return c.json({ access_token: accessToken }, 200)
    } catch {
      return c.json({ error: "Invalid or expired refresh token", status: 401 }, 401)
    }
  })

  // Auth: me
  app.openapi(meRoute, async (c) => {
    const userId = c.get("userId")
    const user = await container.userRepository.findById(userId)
    if (!user) {
      return c.json({ error: "User not found", status: 401 }, 401)
    }
    return c.json(
      {
        id: user.id,
        email: user.email,
        display_name: user.displayName,
        created_at: user.createdAt.toISOString(),
      },
      200,
    )
  })

  return app
}

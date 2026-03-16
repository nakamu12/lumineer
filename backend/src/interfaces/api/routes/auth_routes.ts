import { createRoute } from "@hono/zod-openapi"
import type { OpenAPIHono } from "@hono/zod-openapi"
import type { Container } from "../../../config/container.ts"
import { verifyToken, signToken } from "../../../infrastructure/auth/jwt.ts"
import { ConflictError, UnauthorizedError } from "../../../domain/errors.ts"
import {
  RegisterRequestSchema,
  LoginRequestSchema,
  RefreshRequestSchema,
  AuthResponseSchema,
  RefreshResponseSchema,
  MeResponseSchema,
} from "../schemas/auth.ts"
import { ErrorResponseSchema } from "../schemas/common.ts"
import type { AppVariables } from "../types.ts"

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
      content: { "application/json": { schema: RefreshResponseSchema } },
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

export function registerAuthRoutes(
  app: OpenAPIHono<{ Variables: AppVariables }>,
  container: Container,
): void {
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
      if (err instanceof ConflictError) {
        return c.json({ error: err.message, status: 409 }, 409)
      }
      throw err
    }
  })

  app.openapi(loginRoute, async (c) => {
    const { email, password } = c.req.valid("json")
    try {
      const { user, tokens } = await container.loginUserUseCase.execute({ email, password })
      return c.json(
        {
          user: { id: user.id, email: user.email, display_name: user.displayName },
          access_token: tokens.accessToken,
          refresh_token: tokens.refreshToken,
        },
        200,
      )
    } catch (err) {
      if (err instanceof UnauthorizedError) {
        return c.json({ error: err.message, status: 401 }, 401)
      }
      throw err
    }
  })

  app.openapi(refreshRoute, async (c) => {
    const { refresh_token } = c.req.valid("json")
    try {
      const payload = await verifyToken(refresh_token)
      if (payload.type !== "refresh") {
        return c.json({ error: "Invalid token type", status: 401 }, 401)
      }
      const accessToken = await signToken(payload.sub, "access")
      return c.json({ access_token: accessToken }, 200)
    } catch {
      return c.json({ error: "Invalid or expired refresh token", status: 401 }, 401)
    }
  })

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
}

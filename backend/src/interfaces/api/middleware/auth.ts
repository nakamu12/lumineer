import type { MiddlewareHandler } from "hono"
import type { TokenIssuerPort } from "../../../domain/ports/auth.ts"

// /api/auth/me is intentionally absent — it requires authentication
// /api/chat and /api/search are public until frontend auth is implemented
const PUBLIC_PATHS = [
  "/health",
  "/docs",
  "/openapi.json",
  "/api/auth/register",
  "/api/auth/login",
  "/api/auth/refresh",
  "/api/chat",
  "/api/search",
]

function isPublicPath(path: string): boolean {
  return PUBLIC_PATHS.some((p) => path === p || path.startsWith(`${p}/`))
}

export function createAuthMiddleware(tokenIssuer: TokenIssuerPort): MiddlewareHandler {
  return async (c, next) => {
    if (isPublicPath(c.req.path)) {
      return next()
    }

    const authHeader = c.req.header("Authorization")
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return c.json({ error: "Unauthorized", status: 401 }, 401)
    }

    const token = authHeader.slice(7)
    try {
      const payload = await tokenIssuer.verifyToken(token)
      if (payload.type !== "access") {
        return c.json({ error: "Invalid token type", status: 401 }, 401)
      }
      c.set("userId", payload.sub)
      return next()
    } catch {
      return c.json({ error: "Invalid or expired token", status: 401 }, 401)
    }
  }
}

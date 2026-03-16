import type { MiddlewareHandler } from "hono"
import { verifyToken } from "../../../infrastructure/auth/jwt.ts"

const PUBLIC_PATHS = ["/health", "/docs", "/openapi.json"]
const PUBLIC_PREFIXES = ["/api/auth/"]

function isPublicPath(path: string): boolean {
  if (PUBLIC_PATHS.includes(path)) return true
  return PUBLIC_PREFIXES.some((prefix) => path.startsWith(prefix))
}

export const authMiddleware: MiddlewareHandler = async (c, next) => {
  if (isPublicPath(c.req.path)) {
    return next()
  }

  const authHeader = c.req.header("Authorization")
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return c.json({ error: "Unauthorized", status: 401 }, 401)
  }

  const token = authHeader.slice(7)
  try {
    const payload = await verifyToken(token)
    if (payload.type !== "access") {
      return c.json({ error: "Invalid token type", status: 401 }, 401)
    }
    c.set("userId", payload.sub)
    return next()
  } catch {
    return c.json({ error: "Invalid or expired token", status: 401 }, 401)
  }
}

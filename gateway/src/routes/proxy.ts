import { Hono } from "hono"
import { getSettings } from "../config/settings.ts"

const proxy = new Hono()

/**
 * Proxy all /api/* requests to the backend service.
 * The gateway is the sole public entry point; backend is internal only.
 */
proxy.all("/api/*", async (c) => {
  const { BACKEND_URL } = getSettings()
  const url = new URL(c.req.url)
  const target = `${BACKEND_URL}${url.pathname}${url.search}`

  const reqHeaders = new Headers(c.req.raw.headers)
  // Forward real client IP for downstream logging
  reqHeaders.set("x-forwarded-for", c.req.header("x-forwarded-for") ?? "unknown")

  const response = await fetch(target, {
    method: c.req.method,
    headers: reqHeaders,
    body: ["GET", "HEAD"].includes(c.req.method) ? undefined : c.req.raw.body,
  })

  return new Response(response.body, {
    status: response.status,
    headers: response.headers,
  })
})

export { proxy }

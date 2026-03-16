import type { MiddlewareHandler } from "hono";
import { getSettings } from "../config/settings.ts";

const counters = new Map<string, { count: number; resetAt: number }>();

/**
 * Simple in-process rate limiter.
 * Resets per IP every RATE_LIMIT_WINDOW_MS milliseconds.
 */
export function rateLimiter(): MiddlewareHandler {
  const { RATE_LIMIT_MAX, RATE_LIMIT_WINDOW_MS } = getSettings();

  return async (c, next) => {
    const ip = c.req.header("x-forwarded-for") ?? "unknown";
    const now = Date.now();
    const entry = counters.get(ip);

    if (!entry || now > entry.resetAt) {
      counters.set(ip, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS });
      return next();
    }

    if (entry.count >= RATE_LIMIT_MAX) {
      return c.json({ error: "Too many requests" }, 429);
    }

    entry.count++;
    return next();
  };
}

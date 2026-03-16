import type { Context, Next } from "hono";

export async function errorHandler(c: Context, next: Next): Promise<void> {
  try {
    await next();
  } catch (err) {
    console.error("[ErrorHandler]", err);
    const message =
      err instanceof Error ? err.message : "Internal server error";
    c.res = c.json({ error: message, status: 500 }, 500);
  }
}

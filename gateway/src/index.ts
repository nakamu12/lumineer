import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import { getSettings } from "./config/settings.ts";
import { rateLimiter } from "./middleware/rate_limiter.ts";
import { proxy } from "./routes/proxy.ts";

const settings = getSettings();

const app = new Hono();

// --- Cross-cutting middleware ---
app.use("*", logger());
app.use(
  "*",
  cors({
    origin: settings.ALLOWED_ORIGINS,
    allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization"],
  })
);
app.use("*", rateLimiter());

// --- Health check (no auth required) ---
app.get("/health", (c) => c.json({ status: "ok", service: "gateway" }));

// --- Proxy routes ---
app.route("/", proxy);

// --- 404 fallback ---
app.notFound((c) => c.json({ error: "Not found" }, 404));

export default {
  port: settings.PORT,
  fetch: app.fetch,
};

console.log(`Lumineer Gateway running on port ${settings.PORT}`);

import { Hono } from "hono";

const app = new Hono();

const APP_ENV = process.env.APP_ENV ?? "dev";
const AI_SERVICE_URL = process.env.AI_SERVICE_URL ?? "http://localhost:8001";

app.get("/health", (c) =>
  c.json({ status: "ok", service: "lumineer-api-sample", env: APP_ENV })
);

app.get("/", (c) =>
  c.json({
    message: "Hello from Lumineer API (sample)!",
    env: APP_ENV,
    ai_service_url: AI_SERVICE_URL,
    timestamp: new Date().toISOString(),
  })
);

const port = Number(process.env.PORT ?? 8080);

console.log(`[lumineer-api-sample] listening on port ${port} (env=${APP_ENV})`);

export default { port, fetch: app.fetch };

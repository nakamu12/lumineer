import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import type { Container } from "../../config/container.ts";
import { errorHandler } from "./middleware/error_handler.ts";

const searchSchema = z.object({
  query: z.string().min(1),
  level: z.enum(["Beginner", "Intermediate", "Advanced"]).optional(),
  organization: z.string().optional(),
  min_rating: z.number().min(0).max(5).optional(),
  skills: z.array(z.string()).optional(),
  limit: z.number().int().min(1).max(50).optional(),
});

const chatSchema = z.object({
  message: z.string().min(1),
  session_id: z.string().optional(),
});

export function createRouter(container: Container): Hono {
  const app = new Hono();

  app.use("*", errorHandler);

  app.get("/health", (c) =>
    c.json({ status: "ok", timestamp: new Date().toISOString() })
  );

  app.post("/api/search", zValidator("json", searchSchema), async (c) => {
    const { query, level, organization, min_rating, skills, limit } =
      c.req.valid("json");
    const result = await container.searchCoursesUseCase.execute(query, {
      level,
      organization,
      min_rating,
      skills,
      limit,
    });
    return c.json(result);
  });

  app.post("/api/chat", zValidator("json", chatSchema), async (c) => {
    const { message, session_id } = c.req.valid("json");
    const result = await container.chatUseCase.execute(message, session_id);
    return c.json(result);
  });

  return app;
}

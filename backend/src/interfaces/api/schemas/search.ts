import { z } from "@hono/zod-openapi"

export const SearchRequestSchema = z
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

export const CourseSchema = z
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

export const SearchResponseSchema = z
  .object({
    courses: z.array(CourseSchema),
    summary: z.string(),
    total: z.number(),
  })
  .openapi("SearchResponse")

export const ChatRequestSchema = z
  .object({
    message: z.string().min(1).openapi({ example: "I want to become a data scientist" }),
    session_id: z.string().optional().openapi({ example: "sess_abc123" }),
  })
  .openapi("ChatRequest")

export const ChatResponseSchema = z
  .object({
    message: z.string(),
    courses: z.array(CourseSchema).optional(),
    session_id: z.string(),
  })
  .openapi("ChatResponse")

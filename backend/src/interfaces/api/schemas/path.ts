import { z } from "@hono/zod-openapi"

export const CourseRefSchema = z.object({
  course_id: z.string(),
  order: z.number().int(),
})

export const LearningPathSchema = z
  .object({
    id: z.string().openapi({ example: "550e8400-e29b-41d4-a716-446655440000" }),
    title: z.string().openapi({ example: "Data Science Roadmap" }),
    goal: z.string().nullable().openapi({ example: "Become a data scientist in 3 months" }),
    courses: z.array(CourseRefSchema).openapi({ example: [{ course_id: "abc", order: 1 }] }),
    created_at: z.string().openapi({ example: "2026-03-16T10:00:00.000Z" }),
    updated_at: z.string().openapi({ example: "2026-03-16T10:00:00.000Z" }),
  })
  .openapi("LearningPath")

export const CreatePathRequestSchema = z
  .object({
    title: z.string().min(1).max(200).openapi({ example: "Data Science Roadmap" }),
    goal: z.string().optional().openapi({ example: "Become a data scientist in 3 months" }),
    courses: z
      .array(CourseRefSchema)
      .default([])
      .openapi({ example: [{ course_id: "abc", order: 1 }] }),
  })
  .openapi("CreatePathRequest")

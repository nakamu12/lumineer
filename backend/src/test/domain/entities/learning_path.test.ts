import { describe, it, expect } from "vitest"
import { LearningPathFactory } from "../../../domain/entities/learning_path.ts"

describe("LearningPathFactory", () => {
  const validParams = {
    id: "path-id",
    title: "Data Science Roadmap",
    goal: "Become a data scientist",
    courses: [{ course_id: "abc", order: 1 }],
    createdAt: new Date("2026-03-16T10:00:00Z"),
    updatedAt: new Date("2026-03-16T10:00:00Z"),
  }

  it("creates a valid learning path", () => {
    const path = LearningPathFactory.create(validParams)
    expect(path.title).toBe("Data Science Roadmap")
    expect(path.goal).toBe("Become a data scientist")
    expect(path.courses).toHaveLength(1)
  })

  it("allows null goal", () => {
    const path = LearningPathFactory.create({ ...validParams, goal: null })
    expect(path.goal).toBeNull()
  })

  it("allows empty courses array", () => {
    const path = LearningPathFactory.create({ ...validParams, courses: [] })
    expect(path.courses).toEqual([])
  })

  it("trims title whitespace", () => {
    const path = LearningPathFactory.create({ ...validParams, title: "  Trimmed  " })
    expect(path.title).toBe("Trimmed")
  })

  it("throws on empty title", () => {
    expect(() => LearningPathFactory.create({ ...validParams, title: "" })).toThrow(
      "Learning path title cannot be empty",
    )
  })
})

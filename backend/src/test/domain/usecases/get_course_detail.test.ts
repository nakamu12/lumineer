import { describe, it, expect, vi } from "vitest"
import { GetCourseDetailUseCase } from "../../../domain/usecases/get_course_detail.ts"
import type { AIProcessingPort } from "../../../domain/ports/ai_processing.ts"
import type { Course } from "../../../domain/entities/course.ts"

function createMockAIProcessing(overrides: Partial<AIProcessingPort> = {}): AIProcessingPort {
  return {
    search: vi.fn(),
    chat: vi.fn(),
    chatStream: vi.fn(),
    getCourseById: vi.fn(),
    ...overrides,
  }
}

const mockCourse: Course = {
  id: "course-123",
  title: "Machine Learning",
  description: "Learn ML fundamentals",
  skills: ["Python", "TensorFlow"],
  level: "Beginner",
  organization: "Stanford",
  rating: 4.8,
  enrolled: 12345,
  url: "https://coursera.org/learn/ml",
  modules: "Week 1: Intro",
  schedule: "4 weeks",
  instructor: "Andrew Ng",
}

describe("GetCourseDetailUseCase", () => {
  it("returns course when found", async () => {
    const aiProcessing = createMockAIProcessing({
      getCourseById: vi.fn().mockResolvedValue(mockCourse),
    })
    const useCase = new GetCourseDetailUseCase(aiProcessing)

    const result = await useCase.execute("course-123")

    expect(result).toEqual(mockCourse)
    expect(aiProcessing.getCourseById).toHaveBeenCalledWith("course-123")
  })

  it("returns null when course not found", async () => {
    const aiProcessing = createMockAIProcessing({
      getCourseById: vi.fn().mockResolvedValue(null),
    })
    const useCase = new GetCourseDetailUseCase(aiProcessing)

    const result = await useCase.execute("nonexistent")

    expect(result).toBeNull()
    expect(aiProcessing.getCourseById).toHaveBeenCalledWith("nonexistent")
  })
})

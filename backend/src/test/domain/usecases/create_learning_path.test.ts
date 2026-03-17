import { describe, it, expect, vi } from "vitest"
import { CreateLearningPathUseCase } from "../../../domain/usecases/create_learning_path.ts"
import type { LearningPathRepositoryPort } from "../../../domain/ports/learning_path_repository.ts"

function createMockRepository(
  overrides: Partial<LearningPathRepositoryPort> = {},
): LearningPathRepositoryPort {
  return {
    findByUserId: vi.fn(),
    create: vi.fn(),
    ...overrides,
  }
}

describe("CreateLearningPathUseCase", () => {
  const mockPath = {
    id: "path-1",
    title: "Data Science Roadmap",
    goal: "Become a data scientist",
    courses: [{ course_id: "abc", order: 1 }],
    createdAt: new Date("2026-03-16T10:00:00Z"),
    updatedAt: new Date("2026-03-16T10:00:00Z"),
  }

  it("creates a learning path with all fields", async () => {
    const repo = createMockRepository({
      create: vi.fn().mockResolvedValue(mockPath),
    })
    const useCase = new CreateLearningPathUseCase(repo)

    const input = {
      title: "Data Science Roadmap",
      goal: "Become a data scientist",
      courses: [{ course_id: "abc", order: 1 }],
    }
    const result = await useCase.execute("user-1", input)

    expect(result).toEqual(mockPath)
    expect(repo.create).toHaveBeenCalledWith("user-1", input)
  })

  it("creates a learning path without goal", async () => {
    const pathNoGoal = { ...mockPath, goal: null }
    const repo = createMockRepository({
      create: vi.fn().mockResolvedValue(pathNoGoal),
    })
    const useCase = new CreateLearningPathUseCase(repo)

    const input = {
      title: "Quick Path",
      courses: [] as { course_id: string; order: number }[],
    }
    const result = await useCase.execute("user-1", input)

    expect(result.goal).toBeNull()
  })
})

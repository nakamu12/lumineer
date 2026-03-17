import { describe, it, expect, vi } from "vitest"
import { ListLearningPathsUseCase } from "../../../domain/usecases/list_learning_paths.ts"
import type { LearningPathRepositoryPort } from "../../../domain/ports/learning_path_repository.ts"

function createMockRepository(
  overrides: Partial<LearningPathRepositoryPort> = {},
): LearningPathRepositoryPort {
  return {
    findByUserId: vi.fn().mockResolvedValue([]),
    create: vi.fn(),
    ...overrides,
  }
}

describe("ListLearningPathsUseCase", () => {
  const mockPaths = [
    {
      id: "path-1",
      title: "Data Science Roadmap",
      goal: "Become a data scientist",
      courses: [{ course_id: "abc", order: 1 }],
      createdAt: new Date("2026-03-16T10:00:00Z"),
      updatedAt: new Date("2026-03-16T10:00:00Z"),
    },
  ]

  it("returns learning paths for user", async () => {
    const repo = createMockRepository({
      findByUserId: vi.fn().mockResolvedValue(mockPaths),
    })
    const useCase = new ListLearningPathsUseCase(repo)

    const result = await useCase.execute("user-1")

    expect(result).toEqual(mockPaths)
    expect(repo.findByUserId).toHaveBeenCalledWith("user-1")
  })

  it("returns empty array for user with no paths", async () => {
    const repo = createMockRepository()
    const useCase = new ListLearningPathsUseCase(repo)

    const result = await useCase.execute("user-1")

    expect(result).toEqual([])
  })
})

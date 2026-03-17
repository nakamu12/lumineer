import { describe, it, expect, vi } from "vitest"
import { UpdateUserSettingsUseCase } from "../../../domain/usecases/update_user_settings.ts"
import type { UserSettingsRepositoryPort } from "../../../domain/ports/user_settings_repository.ts"

function createMockRepository(
  overrides: Partial<UserSettingsRepositoryPort> = {},
): UserSettingsRepositoryPort {
  return {
    findOrCreateByUserId: vi.fn(),
    updateByUserId: vi.fn(),
    ...overrides,
  }
}

describe("UpdateUserSettingsUseCase", () => {
  const mockSettings = {
    id: "settings-1",
    rerankerStrategy: "heuristic" as const,
    contextFormat: "toon" as const,
    topK: 20,
    similarityThreshold: 0.8,
  }

  it("delegates to updateByUserId", async () => {
    const repo = createMockRepository({
      updateByUserId: vi.fn().mockResolvedValue(mockSettings),
    })
    const useCase = new UpdateUserSettingsUseCase(repo)

    const result = await useCase.execute("user-1", { rerankerStrategy: "heuristic" })

    expect(result).toEqual(mockSettings)
    expect(repo.updateByUserId).toHaveBeenCalledWith("user-1", {
      rerankerStrategy: "heuristic",
    })
  })

  it("passes partial input to repository", async () => {
    const repo = createMockRepository({
      updateByUserId: vi.fn().mockResolvedValue(mockSettings),
    })
    const useCase = new UpdateUserSettingsUseCase(repo)

    await useCase.execute("user-1", { topK: 20, similarityThreshold: 0.8 })

    expect(repo.updateByUserId).toHaveBeenCalledWith("user-1", {
      topK: 20,
      similarityThreshold: 0.8,
    })
  })
})

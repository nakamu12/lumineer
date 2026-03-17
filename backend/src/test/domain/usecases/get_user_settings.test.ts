import { describe, it, expect, vi } from "vitest"
import { GetUserSettingsUseCase } from "../../../domain/usecases/get_user_settings.ts"
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

describe("GetUserSettingsUseCase", () => {
  const mockSettings = {
    id: "settings-1",
    rerankerStrategy: "none" as const,
    contextFormat: "json" as const,
    topK: 10,
    similarityThreshold: 0.7,
  }

  it("delegates to findOrCreateByUserId", async () => {
    const repo = createMockRepository({
      findOrCreateByUserId: vi.fn().mockResolvedValue(mockSettings),
    })
    const useCase = new GetUserSettingsUseCase(repo)

    const result = await useCase.execute("user-1")

    expect(result).toEqual(mockSettings)
    expect(repo.findOrCreateByUserId).toHaveBeenCalledWith("user-1")
  })

  it("returns default settings for new user", async () => {
    const defaultSettings = { ...mockSettings, id: "new-settings" }
    const repo = createMockRepository({
      findOrCreateByUserId: vi.fn().mockResolvedValue(defaultSettings),
    })
    const useCase = new GetUserSettingsUseCase(repo)

    const result = await useCase.execute("new-user")

    expect(result.rerankerStrategy).toBe("none")
    expect(result.contextFormat).toBe("json")
    expect(result.topK).toBe(10)
    expect(result.similarityThreshold).toBe(0.7)
  })
})

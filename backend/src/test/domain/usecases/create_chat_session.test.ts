import { describe, it, expect, vi } from "vitest"
import { CreateChatSessionUseCase } from "../../../domain/usecases/create_chat_session.ts"
import type { ChatSessionRepositoryPort } from "../../../domain/ports/chat_session_repository.ts"

function createMockRepository(
  overrides: Partial<ChatSessionRepositoryPort> = {},
): ChatSessionRepositoryPort {
  return {
    findByUserId: vi.fn(),
    create: vi.fn(),
    findByIdAndUserId: vi.fn(),
    findMessagesBySessionId: vi.fn(),
    saveMessage: vi.fn(),
    updateSessionTitle: vi.fn(),
    ...overrides,
  }
}

describe("CreateChatSessionUseCase", () => {
  const mockSession = {
    id: "session-1",
    title: "My Chat",
    createdAt: new Date("2026-03-16T10:00:00Z"),
    updatedAt: new Date("2026-03-16T10:00:00Z"),
  }

  it("creates a session with provided title", async () => {
    const repo = createMockRepository({
      create: vi.fn().mockResolvedValue(mockSession),
    })
    const useCase = new CreateChatSessionUseCase(repo)

    const result = await useCase.execute("user-1", "My Chat")

    expect(result).toEqual(mockSession)
    expect(repo.create).toHaveBeenCalledWith("user-1", "My Chat")
  })

  it("creates a session without title", async () => {
    const defaultSession = { ...mockSession, title: "New Chat" }
    const repo = createMockRepository({
      create: vi.fn().mockResolvedValue(defaultSession),
    })
    const useCase = new CreateChatSessionUseCase(repo)

    const result = await useCase.execute("user-1")

    expect(result.title).toBe("New Chat")
    expect(repo.create).toHaveBeenCalledWith("user-1", undefined)
  })
})

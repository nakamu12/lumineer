import { describe, it, expect, vi } from "vitest"
import { ListChatSessionsUseCase } from "../../../domain/usecases/list_chat_sessions.ts"
import type { ChatSessionRepositoryPort } from "../../../domain/ports/chat_session_repository.ts"

function createMockRepository(
  overrides: Partial<ChatSessionRepositoryPort> = {},
): ChatSessionRepositoryPort {
  return {
    findByUserId: vi.fn().mockResolvedValue([]),
    create: vi.fn(),
    findByIdAndUserId: vi.fn(),
    findMessagesBySessionId: vi.fn(),
    ...overrides,
  }
}

describe("ListChatSessionsUseCase", () => {
  const mockSessions = [
    {
      id: "session-1",
      title: "First Chat",
      createdAt: new Date("2026-03-16T10:00:00Z"),
      updatedAt: new Date("2026-03-16T10:00:00Z"),
    },
    {
      id: "session-2",
      title: "Second Chat",
      createdAt: new Date("2026-03-16T11:00:00Z"),
      updatedAt: new Date("2026-03-16T11:00:00Z"),
    },
  ]

  it("returns sessions for user", async () => {
    const repo = createMockRepository({
      findByUserId: vi.fn().mockResolvedValue(mockSessions),
    })
    const useCase = new ListChatSessionsUseCase(repo)

    const result = await useCase.execute("user-1")

    expect(result).toEqual(mockSessions)
    expect(repo.findByUserId).toHaveBeenCalledWith("user-1")
  })

  it("returns empty array for user with no sessions", async () => {
    const repo = createMockRepository({
      findByUserId: vi.fn().mockResolvedValue([]),
    })
    const useCase = new ListChatSessionsUseCase(repo)

    const result = await useCase.execute("user-1")

    expect(result).toEqual([])
  })
})

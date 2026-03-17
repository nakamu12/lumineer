import { describe, it, expect, vi } from "vitest"
import { ListChatMessagesUseCase } from "../../../domain/usecases/list_chat_messages.ts"
import type { ChatSessionRepositoryPort } from "../../../domain/ports/chat_session_repository.ts"

function createMockRepository(
  overrides: Partial<ChatSessionRepositoryPort> = {},
): ChatSessionRepositoryPort {
  return {
    findByUserId: vi.fn(),
    create: vi.fn(),
    findByIdAndUserId: vi.fn().mockResolvedValue(null),
    findMessagesBySessionId: vi.fn().mockResolvedValue([]),
    ...overrides,
  }
}

describe("ListChatMessagesUseCase", () => {
  const mockSession = {
    id: "session-1",
    title: "Test Chat",
    createdAt: new Date(),
    updatedAt: new Date(),
  }

  const mockMessages = [
    {
      id: "msg-1",
      sessionId: "session-1",
      role: "user" as const,
      content: "Hello",
      createdAt: new Date(),
    },
    {
      id: "msg-2",
      sessionId: "session-1",
      role: "assistant" as const,
      content: "Hi there!",
      createdAt: new Date(),
    },
  ]

  it("returns messages when session belongs to user", async () => {
    const repo = createMockRepository({
      findByIdAndUserId: vi.fn().mockResolvedValue(mockSession),
      findMessagesBySessionId: vi.fn().mockResolvedValue(mockMessages),
    })
    const useCase = new ListChatMessagesUseCase(repo)

    const result = await useCase.execute("user-1", "session-1")

    expect(result).toEqual(mockMessages)
    expect(repo.findByIdAndUserId).toHaveBeenCalledWith("session-1", "user-1")
    expect(repo.findMessagesBySessionId).toHaveBeenCalledWith("session-1")
  })

  it("throws when session does not exist", async () => {
    const repo = createMockRepository({
      findByIdAndUserId: vi.fn().mockResolvedValue(null),
    })
    const useCase = new ListChatMessagesUseCase(repo)

    await expect(useCase.execute("user-1", "nonexistent")).rejects.toThrow("Chat session not found")
    expect(repo.findMessagesBySessionId).not.toHaveBeenCalled()
  })

  it("throws when session belongs to different user", async () => {
    const repo = createMockRepository({
      findByIdAndUserId: vi.fn().mockResolvedValue(null),
    })
    const useCase = new ListChatMessagesUseCase(repo)

    await expect(useCase.execute("other-user", "session-1")).rejects.toThrow(
      "Chat session not found",
    )
  })
})

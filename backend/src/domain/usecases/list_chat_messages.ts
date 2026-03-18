import type { ChatSessionRepositoryPort } from "../ports/chat_session_repository.ts"
import type { ChatMessageEntity } from "../entities/chat_session.ts"
import { NotFoundError } from "../errors.ts"

export class ListChatMessagesUseCase {
  constructor(private readonly chatSessionRepository: ChatSessionRepositoryPort) {}

  async execute(userId: string, sessionId: string): Promise<ChatMessageEntity[]> {
    const session = await this.chatSessionRepository.findByIdAndUserId(sessionId, userId)
    if (!session) {
      throw new NotFoundError("Chat session not found")
    }
    return this.chatSessionRepository.findMessagesBySessionId(sessionId)
  }
}

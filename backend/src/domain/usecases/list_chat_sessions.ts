import type { ChatSessionRepositoryPort } from "../ports/chat_session_repository.ts"
import type { ChatSessionEntity } from "../entities/chat_session.ts"

export class ListChatSessionsUseCase {
  constructor(private readonly chatSessionRepository: ChatSessionRepositoryPort) {}

  async execute(userId: string): Promise<ChatSessionEntity[]> {
    return this.chatSessionRepository.findByUserId(userId)
  }
}

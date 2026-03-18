import type { ChatSessionRepositoryPort } from "../ports/chat_session_repository.ts"
import type { ChatSessionEntity } from "../entities/chat_session.ts"

export class CreateChatSessionUseCase {
  constructor(private readonly chatSessionRepository: ChatSessionRepositoryPort) {}

  async execute(userId: string, title?: string): Promise<ChatSessionEntity> {
    return this.chatSessionRepository.create(userId, title)
  }
}

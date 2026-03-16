import type { ChatSessionEntity, ChatMessageEntity } from "../entities/chat_session.ts"

export interface ChatSessionRepositoryPort {
  findByUserId(userId: string): Promise<ChatSessionEntity[]>
  create(userId: string, title?: string): Promise<ChatSessionEntity>
  findByIdAndUserId(id: string, userId: string): Promise<ChatSessionEntity | null>
  findMessagesBySessionId(sessionId: string): Promise<ChatMessageEntity[]>
}

import type { AIProcessingPort, ChatResult } from "../ports/ai_processing.ts"
import type { ChatSessionRepositoryPort } from "../ports/chat_session_repository.ts"

export class ChatUseCase {
  constructor(
    private readonly aiProcessing: AIProcessingPort,
    private readonly chatSessionRepository: ChatSessionRepositoryPort,
  ) {}

  async execute(message: string, sessionId?: string): Promise<ChatResult> {
    return this.aiProcessing.chat(message, sessionId)
  }

  async getStream(
    message: string,
    sessionId?: string,
    userId?: string,
  ): Promise<{ response: Response; sessionId: string | null }> {
    const resolvedSessionId = userId ? await this.resolveAndSave(userId, sessionId, message) : null

    const response = await this.aiProcessing.chatStream(message, resolvedSessionId ?? undefined)

    return { response, sessionId: resolvedSessionId }
  }

  async saveAssistantMessage(sessionId: string, content: string): Promise<void> {
    if (content.trim().length === 0) return
    await this.chatSessionRepository.saveMessage(sessionId, "assistant", content)
  }

  private async resolveAndSave(
    userId: string,
    sessionId: string | undefined,
    message: string,
  ): Promise<string> {
    if (sessionId) {
      const existing = await this.chatSessionRepository.findByIdAndUserId(sessionId, userId)
      if (existing) {
        await this.chatSessionRepository.saveMessage(existing.id, "user", message)
        return existing.id
      }
    }

    const title = message.length > 50 ? `${message.slice(0, 47)}...` : message
    const session = await this.chatSessionRepository.create(userId, title)
    await this.chatSessionRepository.saveMessage(session.id, "user", message)
    return session.id
  }
}

import type { AIProcessingPort, ChatResult } from "../ports/ai_processing.ts"

export class ChatUseCase {
  constructor(private readonly aiProcessing: AIProcessingPort) {}

  async execute(message: string, sessionId?: string): Promise<ChatResult> {
    return this.aiProcessing.chat(message, sessionId)
  }
}

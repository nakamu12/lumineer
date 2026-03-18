export type ChatSessionEntity = {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
}

export type ChatMessageEntity = {
  id: string
  sessionId: string
  role: "user" | "assistant"
  content: string
  createdAt: Date
}

type CreateChatSessionParams = {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
}

type CreateChatMessageParams = {
  id: string
  sessionId: string
  role: string
  content: string
  createdAt: Date
}

const VALID_ROLES = new Set(["user", "assistant"])

export const ChatSessionFactory = {
  create(params: CreateChatSessionParams): ChatSessionEntity {
    const title = params.title.trim()
    if (title.length === 0) {
      throw new Error("Chat session title cannot be empty")
    }
    return {
      id: params.id,
      title,
      createdAt: params.createdAt,
      updatedAt: params.updatedAt,
    }
  },
}

export const ChatMessageFactory = {
  create(params: CreateChatMessageParams): ChatMessageEntity {
    if (!VALID_ROLES.has(params.role)) {
      throw new Error(`Invalid message role: ${params.role}`)
    }
    if (!params.content || params.content.trim().length === 0) {
      throw new Error("Message content cannot be empty")
    }
    return {
      id: params.id,
      sessionId: params.sessionId,
      role: params.role as "user" | "assistant",
      content: params.content,
      createdAt: params.createdAt,
    }
  },
}

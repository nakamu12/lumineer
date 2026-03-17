import { eq, and, desc, asc } from "drizzle-orm"
import type { ChatSessionRepositoryPort } from "../../domain/ports/chat_session_repository.ts"
import type { ChatSessionEntity, ChatMessageEntity } from "../../domain/entities/chat_session.ts"
import { ChatSessionFactory, ChatMessageFactory } from "../../domain/entities/chat_session.ts"
import { getDb } from "./client.ts"
import { chatSessions, chatMessages } from "./schema.ts"

export class DrizzleChatSessionRepository implements ChatSessionRepositoryPort {
  async findByUserId(userId: string): Promise<ChatSessionEntity[]> {
    const db = getDb()
    const rows = await db
      .select()
      .from(chatSessions)
      .where(eq(chatSessions.userId, userId))
      .orderBy(desc(chatSessions.createdAt))
    return rows.map((row) =>
      ChatSessionFactory.create({
        id: row.id,
        title: row.title,
        createdAt: row.createdAt,
        updatedAt: row.updatedAt,
      }),
    )
  }

  async create(userId: string, title?: string): Promise<ChatSessionEntity> {
    const db = getDb()
    const rows = await db
      .insert(chatSessions)
      .values({
        userId,
        ...(title ? { title: title.trim() } : {}),
      })
      .returning()
    const row = rows[0]
    if (!row) throw new Error("Failed to create chat session")
    return ChatSessionFactory.create({
      id: row.id,
      title: row.title,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    })
  }

  async findByIdAndUserId(id: string, userId: string): Promise<ChatSessionEntity | null> {
    const db = getDb()
    const rows = await db
      .select()
      .from(chatSessions)
      .where(and(eq(chatSessions.id, id), eq(chatSessions.userId, userId)))
      .limit(1)
    const row = rows[0]
    if (!row) return null
    return ChatSessionFactory.create({
      id: row.id,
      title: row.title,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    })
  }

  async findMessagesBySessionId(sessionId: string): Promise<ChatMessageEntity[]> {
    const db = getDb()
    const rows = await db
      .select()
      .from(chatMessages)
      .where(eq(chatMessages.sessionId, sessionId))
      .orderBy(asc(chatMessages.createdAt))
    return rows.map((row) =>
      ChatMessageFactory.create({
        id: row.id,
        sessionId: row.sessionId,
        role: row.role,
        content: row.content,
        createdAt: row.createdAt,
      }),
    )
  }

  async saveMessage(
    sessionId: string,
    role: "user" | "assistant",
    content: string,
  ): Promise<ChatMessageEntity> {
    const db = getDb()
    const rows = await db.insert(chatMessages).values({ sessionId, role, content }).returning()
    const row = rows[0]
    if (!row) throw new Error("Failed to save chat message")
    return ChatMessageFactory.create({
      id: row.id,
      sessionId: row.sessionId,
      role: row.role,
      content: row.content,
      createdAt: row.createdAt,
    })
  }

  async updateSessionTitle(sessionId: string, title: string): Promise<void> {
    const db = getDb()
    await db
      .update(chatSessions)
      .set({ title: title.trim(), updatedAt: new Date() })
      .where(eq(chatSessions.id, sessionId))
  }
}

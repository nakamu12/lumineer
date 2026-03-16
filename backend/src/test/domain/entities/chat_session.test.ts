import { describe, it, expect } from "vitest"
import { ChatSessionFactory, ChatMessageFactory } from "../../../domain/entities/chat_session.ts"

describe("ChatSessionFactory", () => {
  const validParams = {
    id: "test-id",
    title: "My Chat",
    createdAt: new Date("2026-03-16T10:00:00Z"),
    updatedAt: new Date("2026-03-16T10:00:00Z"),
  }

  it("creates a valid chat session", () => {
    const session = ChatSessionFactory.create(validParams)
    expect(session.id).toBe("test-id")
    expect(session.title).toBe("My Chat")
    expect(session.createdAt).toEqual(validParams.createdAt)
  })

  it("trims whitespace from title", () => {
    const session = ChatSessionFactory.create({ ...validParams, title: "  Trimmed  " })
    expect(session.title).toBe("Trimmed")
  })

  it("throws on empty title", () => {
    expect(() => ChatSessionFactory.create({ ...validParams, title: "" })).toThrow(
      "Chat session title cannot be empty",
    )
  })

  it("throws on whitespace-only title", () => {
    expect(() => ChatSessionFactory.create({ ...validParams, title: "   " })).toThrow(
      "Chat session title cannot be empty",
    )
  })
})

describe("ChatMessageFactory", () => {
  const validParams = {
    id: "msg-id",
    sessionId: "session-id",
    role: "user",
    content: "Hello",
    createdAt: new Date("2026-03-16T10:00:00Z"),
  }

  it("creates a valid user message", () => {
    const msg = ChatMessageFactory.create(validParams)
    expect(msg.role).toBe("user")
    expect(msg.content).toBe("Hello")
  })

  it("creates a valid assistant message", () => {
    const msg = ChatMessageFactory.create({ ...validParams, role: "assistant" })
    expect(msg.role).toBe("assistant")
  })

  it("throws on invalid role", () => {
    expect(() => ChatMessageFactory.create({ ...validParams, role: "system" })).toThrow(
      "Invalid message role: system",
    )
  })

  it("throws on empty content", () => {
    expect(() => ChatMessageFactory.create({ ...validParams, content: "" })).toThrow(
      "Message content cannot be empty",
    )
  })
})

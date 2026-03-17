import { useState, useRef, useCallback } from "react"
import type { ChatMessageData } from "../components/ChatMessage"
import type { Course } from "@/lib/types/course"

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:3000"

function generateId() {
  return Math.random().toString(36).slice(2)
}

type SSEEvent = {
  type: "text" | "courses" | "done" | "error" | "session"
  content?: string
  courses?: Course[]
  session_id?: string
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessageData[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(() => {
    return localStorage.getItem("lumineer_chat_session_id")
  })
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading || isStreaming) return

      const userMessage: ChatMessageData = {
        id: generateId(),
        role: "user",
        content: text.trim(),
        timestamp: new Date(),
      }

      const assistantId = generateId()
      const assistantMessage: ChatMessageData = {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMessage, assistantMessage])
      setIsLoading(true)

      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      try {
        const res = await fetch(`${API_URL}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: text.trim(),
            session_id: sessionId ?? undefined,
          }),
          signal: controller.signal,
        })

        if (!res.ok || !res.body) {
          throw new Error(`HTTP ${res.status}`)
        }

        setIsLoading(false)
        setIsStreaming(true)

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ""

        while (true) {
          const { value, done } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split("\n")
          buffer = lines.pop() ?? ""

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue
            const raw = line.slice(6).trim()
            if (!raw || raw === "[DONE]") continue

            try {
              const event = JSON.parse(raw) as SSEEvent

              if (event.type === "session" && event.session_id) {
                setSessionId(event.session_id)
                localStorage.setItem("lumineer_chat_session_id", event.session_id)
              } else if (event.type === "text" && event.content) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, content: m.content + event.content } : m,
                  ),
                )
              } else if (event.type === "courses" && event.courses) {
                setMessages((prev) =>
                  prev.map((m) => (m.id === assistantId ? { ...m, courses: event.courses } : m)),
                )
              } else if (event.type === "done") {
                break
              } else if (event.type === "error") {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, content: event.content ?? "An error occurred." }
                      : m,
                  ),
                )
                break
              }
            } catch {
              // skip malformed SSE lines
            }
          }
        }
      } catch (err) {
        if ((err as Error).name === "AbortError") return

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: m.content || "Sorry, something went wrong. Please try again.",
                }
              : m,
          ),
        )
      } finally {
        setIsLoading(false)
        setIsStreaming(false)
      }
    },
    [isLoading, isStreaming, sessionId],
  )

  const clearChat = useCallback(() => {
    abortRef.current?.abort()
    setMessages([])
    setSessionId(null)
    localStorage.removeItem("lumineer_chat_session_id")
    setIsLoading(false)
    setIsStreaming(false)
  }, [])

  const loadSession = useCallback(async (targetSessionId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/chat/sessions/${targetSessionId}/messages`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const data = (await res.json()) as Array<{
        id: string
        role: "user" | "assistant"
        content: string
        created_at: string
      }>

      const loaded: ChatMessageData[] = data.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: new Date(m.created_at),
      }))

      setMessages(loaded)
      setSessionId(targetSessionId)
      localStorage.setItem("lumineer_chat_session_id", targetSessionId)
    } catch {
      // session may not exist, start fresh
    }
  }, [])

  return { messages, isLoading, isStreaming, sessionId, sendMessage, clearChat, loadSession }
}

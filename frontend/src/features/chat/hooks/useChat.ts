import { useState, useRef, useCallback } from "react"
import type { ChatMessageData } from "../components/ChatMessage"
import type { Course } from "@/lib/types/course"
import { getAuthHeaders } from "@/lib/auth/token-store"

const API_URL = import.meta.env.VITE_API_URL ?? ""

function generateId() {
  return Math.random().toString(36).slice(2)
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessageData[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
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
          headers: { "Content-Type": "application/json", ...getAuthHeaders() },
          body: JSON.stringify({ message: text.trim() }),
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
              const event = JSON.parse(raw) as {
                type: "text" | "courses" | "done"
                content?: string
                courses?: Course[]
              }

              if (event.type === "text" && event.content) {
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
    [isLoading, isStreaming],
  )

  const clearChat = useCallback(() => {
    abortRef.current?.abort()
    setMessages([])
    setIsLoading(false)
    setIsStreaming(false)
  }, [])

  return { messages, isLoading, isStreaming, sendMessage, clearChat }
}

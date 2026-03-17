import { useState, useEffect, useCallback } from "react"

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:3000"

export type ChatSession = {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [isLoadingSessions, setIsLoadingSessions] = useState(false)

  const fetchSessions = useCallback(async () => {
    setIsLoadingSessions(true)
    try {
      const res = await fetch(`${API_URL}/api/chat/sessions`)
      if (!res.ok) return
      const data = (await res.json()) as ChatSession[]
      setSessions(data)
    } catch {
      // ignore fetch errors
    } finally {
      setIsLoadingSessions(false)
    }
  }, [])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  return { sessions, isLoadingSessions, refreshSessions: fetchSessions }
}

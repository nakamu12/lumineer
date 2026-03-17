import type { Course } from "../entities/course.ts"

export type SearchFilters = {
  level?: "Beginner" | "Intermediate" | "Advanced"
  organization?: string
  min_rating?: number
  skills?: string[]
  limit?: number
}

export type SearchResult = {
  courses: Course[]
  summary: string
  total: number
}

export type ChatResult = {
  message: string
  courses?: Course[]
  session_id: string
}

/**
 * Port for AI Processing Layer communication.
 * Implementations live in infrastructure/llm/.
 */
export interface AIProcessingPort {
  search(query: string, filters?: SearchFilters): Promise<SearchResult>
  chat(message: string, sessionId?: string): Promise<ChatResult>
  chatStream(message: string, sessionId?: string): Promise<Response>
}

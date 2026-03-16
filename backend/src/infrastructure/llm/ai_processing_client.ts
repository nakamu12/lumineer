import { CourseFactory } from "../../domain/entities/course.ts"
import type {
  AIProcessingPort,
  ChatResult,
  SearchFilters,
  SearchResult,
} from "../../domain/ports/ai_processing.ts"
import { getSettings } from "../../config/settings.ts"

export class AIProcessingClient implements AIProcessingPort {
  private readonly baseUrl: string

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl ?? getSettings().AI_PROCESSING_URL
  }

  async search(query: string, filters?: SearchFilters): Promise<SearchResult> {
    const response = await fetch(`${this.baseUrl}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, ...filters }),
    })

    if (!response.ok) {
      throw new Error(`AI Processing search failed: ${response.status} ${response.statusText}`)
    }

    const data = (await response.json()) as {
      courses: unknown[]
      summary: string
      total: number
    }

    return {
      courses: data.courses.map((c) =>
        CourseFactory.create(c as Parameters<typeof CourseFactory.create>[0]),
      ),
      summary: data.summary,
      total: data.total,
    }
  }

  async chat(message: string, sessionId?: string): Promise<ChatResult> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    })

    if (!response.ok) {
      throw new Error(`AI Processing chat failed: ${response.status} ${response.statusText}`)
    }

    const data = (await response.json()) as {
      message: string
      courses?: unknown[]
      session_id: string
    }

    return {
      message: data.message,
      courses: data.courses?.map((c) =>
        CourseFactory.create(c as Parameters<typeof CourseFactory.create>[0]),
      ),
      session_id: data.session_id,
    }
  }
}

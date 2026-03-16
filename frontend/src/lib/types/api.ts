export interface ApiError {
  message: string
  code?: string
}

export interface ApiResponse<T> {
  data?: T
  error?: ApiError
}

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export interface AppSettings {
  reranker_strategy: "none" | "heuristic" | "cross-encoder"
  context_format: "json" | "toon"
  top_k: 5 | 10 | 20
  similarity_threshold: number
}

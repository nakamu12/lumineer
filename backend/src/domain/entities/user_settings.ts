export type RerankerStrategy = "none" | "heuristic" | "cross-encoder"
export type ContextFormat = "json" | "toon"

export type UserSettingsEntity = {
  id: string
  rerankerStrategy: RerankerStrategy
  contextFormat: ContextFormat
  topK: number
  similarityThreshold: number
}

type CreateUserSettingsParams = {
  id: string
  rerankerStrategy: string
  contextFormat: string
  topK: number
  similarityThreshold: number
}

const VALID_RERANKER_STRATEGIES = new Set<string>(["none", "heuristic", "cross-encoder"])
const VALID_CONTEXT_FORMATS = new Set<string>(["json", "toon"])
const VALID_TOP_K_VALUES = new Set([5, 10, 20])

export const UserSettingsFactory = {
  create(params: CreateUserSettingsParams): UserSettingsEntity {
    if (!VALID_RERANKER_STRATEGIES.has(params.rerankerStrategy)) {
      throw new Error(`Invalid reranker strategy: ${params.rerankerStrategy}`)
    }
    if (!VALID_CONTEXT_FORMATS.has(params.contextFormat)) {
      throw new Error(`Invalid context format: ${params.contextFormat}`)
    }
    if (!VALID_TOP_K_VALUES.has(params.topK)) {
      throw new Error(`Invalid top_k value: ${params.topK}. Must be 5, 10, or 20`)
    }
    if (params.similarityThreshold < 0.5 || params.similarityThreshold > 0.9) {
      throw new Error(
        `Invalid similarity threshold: ${params.similarityThreshold}. Must be between 0.5 and 0.9`,
      )
    }
    return {
      id: params.id,
      rerankerStrategy: params.rerankerStrategy as RerankerStrategy,
      contextFormat: params.contextFormat as ContextFormat,
      topK: params.topK,
      similarityThreshold: params.similarityThreshold,
    }
  },
}

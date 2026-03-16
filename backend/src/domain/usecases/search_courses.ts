import type { AIProcessingPort, SearchFilters, SearchResult } from "../ports/ai_processing.ts"

export class SearchCoursesUseCase {
  constructor(private readonly aiProcessing: AIProcessingPort) {}

  async execute(query: string, filters?: SearchFilters): Promise<SearchResult> {
    return this.aiProcessing.search(query, filters)
  }
}

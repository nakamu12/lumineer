import type { LearningPathRepositoryPort } from "../ports/learning_path_repository.ts"
import type { LearningPathEntity } from "../entities/learning_path.ts"

export class ListLearningPathsUseCase {
  constructor(private readonly learningPathRepository: LearningPathRepositoryPort) {}

  async execute(userId: string): Promise<LearningPathEntity[]> {
    return this.learningPathRepository.findByUserId(userId)
  }
}

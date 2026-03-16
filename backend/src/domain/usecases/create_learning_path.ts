import type {
  LearningPathRepositoryPort,
  CreateLearningPathInput,
} from "../ports/learning_path_repository.ts"
import type { LearningPathEntity } from "../entities/learning_path.ts"

export class CreateLearningPathUseCase {
  constructor(private readonly learningPathRepository: LearningPathRepositoryPort) {}

  async execute(userId: string, input: CreateLearningPathInput): Promise<LearningPathEntity> {
    return this.learningPathRepository.create(userId, input)
  }
}

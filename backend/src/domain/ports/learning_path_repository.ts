import type { LearningPathEntity, CourseRef } from "../entities/learning_path.ts"

export type CreateLearningPathInput = {
  title: string
  goal?: string
  courses: CourseRef[]
}

export interface LearningPathRepositoryPort {
  findByUserId(userId: string): Promise<LearningPathEntity[]>
  create(userId: string, input: CreateLearningPathInput): Promise<LearningPathEntity>
}

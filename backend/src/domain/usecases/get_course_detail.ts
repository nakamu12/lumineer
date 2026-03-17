import type { Course } from "../entities/course.ts"
import type { AIProcessingPort } from "../ports/ai_processing.ts"

export class GetCourseDetailUseCase {
  constructor(private readonly aiProcessing: AIProcessingPort) {}

  async execute(courseId: string): Promise<Course | null> {
    return this.aiProcessing.getCourseById(courseId)
  }
}

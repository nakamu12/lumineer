import { eq, desc } from "drizzle-orm"
import type {
  LearningPathRepositoryPort,
  CreateLearningPathInput,
} from "../../domain/ports/learning_path_repository.ts"
import type { LearningPathEntity, CourseRef } from "../../domain/entities/learning_path.ts"
import { LearningPathFactory } from "../../domain/entities/learning_path.ts"
import { getDb } from "./client.ts"
import { learningPaths } from "./schema.ts"

export class DrizzleLearningPathRepository implements LearningPathRepositoryPort {
  async findByUserId(userId: string): Promise<LearningPathEntity[]> {
    const db = getDb()
    const rows = await db
      .select()
      .from(learningPaths)
      .where(eq(learningPaths.userId, userId))
      .orderBy(desc(learningPaths.createdAt))
    return rows.map((row) =>
      LearningPathFactory.create({
        id: row.id,
        title: row.title,
        goal: row.goal,
        courses: row.courses as CourseRef[],
        createdAt: row.createdAt,
        updatedAt: row.updatedAt,
      }),
    )
  }

  async create(userId: string, input: CreateLearningPathInput): Promise<LearningPathEntity> {
    const db = getDb()
    const rows = await db
      .insert(learningPaths)
      .values({
        userId,
        title: input.title.trim(),
        goal: input.goal ?? null,
        courses: input.courses,
      })
      .returning()
    const row = rows[0]
    if (!row) throw new Error("Failed to create learning path")
    return LearningPathFactory.create({
      id: row.id,
      title: row.title,
      goal: row.goal,
      courses: row.courses as CourseRef[],
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    })
  }
}

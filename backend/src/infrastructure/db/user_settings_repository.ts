import { eq } from "drizzle-orm"
import type {
  UserSettingsRepositoryPort,
  UpdateUserSettingsInput,
} from "../../domain/ports/user_settings_repository.ts"
import type { UserSettingsEntity } from "../../domain/entities/user_settings.ts"
import { UserSettingsFactory } from "../../domain/entities/user_settings.ts"
import { getDb } from "./client.ts"
import { userSettings } from "./schema.ts"

export class DrizzleUserSettingsRepository implements UserSettingsRepositoryPort {
  async findOrCreateByUserId(userId: string): Promise<UserSettingsEntity> {
    const db = getDb()

    const existing = await db
      .select()
      .from(userSettings)
      .where(eq(userSettings.userId, userId))
      .limit(1)

    if (existing[0]) {
      return this.toEntity(existing[0])
    }

    // Insert with defaults, handle race condition on unique userId
    await db
      .insert(userSettings)
      .values({ userId })
      .onConflictDoNothing({ target: userSettings.userId })

    // Always re-select to get the row (whether we inserted or lost the race)
    const rows = await db
      .select()
      .from(userSettings)
      .where(eq(userSettings.userId, userId))
      .limit(1)
    const row = rows[0]
    if (!row) throw new Error("Failed to create user settings")
    return this.toEntity(row)
  }

  async updateByUserId(
    userId: string,
    input: UpdateUserSettingsInput,
  ): Promise<UserSettingsEntity> {
    const db = getDb()
    const updateValues: Partial<typeof userSettings.$inferInsert> = {}

    if (input.rerankerStrategy !== undefined) {
      updateValues.rerankerStrategy = input.rerankerStrategy
    }
    if (input.contextFormat !== undefined) {
      updateValues.contextFormat = input.contextFormat
    }
    if (input.topK !== undefined) {
      updateValues.topK = input.topK
    }
    if (input.similarityThreshold !== undefined) {
      updateValues.similarityThreshold = input.similarityThreshold
    }

    if (Object.keys(updateValues).length === 0) {
      return this.findOrCreateByUserId(userId)
    }

    // Ensure settings row exists before updating (atomic: findOrCreate + update)
    await this.findOrCreateByUserId(userId)

    const rows = await db
      .update(userSettings)
      .set(updateValues)
      .where(eq(userSettings.userId, userId))
      .returning()
    const row = rows[0]
    if (!row) throw new Error("User settings not found")
    return this.toEntity(row)
  }

  private toEntity(row: typeof userSettings.$inferSelect): UserSettingsEntity {
    return UserSettingsFactory.create({
      id: row.id,
      rerankerStrategy: row.rerankerStrategy,
      contextFormat: row.contextFormat,
      topK: row.topK,
      similarityThreshold: row.similarityThreshold,
    })
  }
}

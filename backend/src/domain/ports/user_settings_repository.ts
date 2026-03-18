import type { UserSettingsEntity } from "../entities/user_settings.ts"

export type UpdateUserSettingsInput = {
  rerankerStrategy?: string
  contextFormat?: string
  topK?: number
  similarityThreshold?: number
}

export interface UserSettingsRepositoryPort {
  findOrCreateByUserId(userId: string): Promise<UserSettingsEntity>
  updateByUserId(userId: string, input: UpdateUserSettingsInput): Promise<UserSettingsEntity>
}

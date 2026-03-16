import type { UserSettingsRepositoryPort } from "../ports/user_settings_repository.ts"
import type { UserSettingsEntity } from "../entities/user_settings.ts"

export class GetUserSettingsUseCase {
  constructor(private readonly userSettingsRepository: UserSettingsRepositoryPort) {}

  async execute(userId: string): Promise<UserSettingsEntity> {
    return this.userSettingsRepository.findOrCreateByUserId(userId)
  }
}

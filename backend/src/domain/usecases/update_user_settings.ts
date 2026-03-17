import type {
  UserSettingsRepositoryPort,
  UpdateUserSettingsInput,
} from "../ports/user_settings_repository.ts"
import type { UserSettingsEntity } from "../entities/user_settings.ts"

export class UpdateUserSettingsUseCase {
  constructor(private readonly userSettingsRepository: UserSettingsRepositoryPort) {}

  async execute(userId: string, input: UpdateUserSettingsInput): Promise<UserSettingsEntity> {
    return this.userSettingsRepository.updateByUserId(userId, input)
  }
}

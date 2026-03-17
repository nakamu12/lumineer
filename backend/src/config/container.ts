import { AIProcessingClient } from "../infrastructure/llm/ai_processing_client.ts"
import { SearchCoursesUseCase } from "../domain/usecases/search_courses.ts"
import { ChatUseCase } from "../domain/usecases/chat.ts"
import { DrizzleUserRepository } from "../infrastructure/db/user_repository.ts"
import { BcryptPasswordHasher } from "../infrastructure/auth/password.ts"
import { JoseTokenIssuer } from "../infrastructure/auth/jwt.ts"
import { RegisterUserUseCase } from "../domain/usecases/register_user.ts"
import { LoginUserUseCase } from "../domain/usecases/login_user.ts"
import { RefreshTokenUseCase } from "../domain/usecases/refresh_token.ts"
import { DrizzleChatSessionRepository } from "../infrastructure/db/chat_session_repository.ts"
import { DrizzleLearningPathRepository } from "../infrastructure/db/learning_path_repository.ts"
import { DrizzleUserSettingsRepository } from "../infrastructure/db/user_settings_repository.ts"
import { ListChatSessionsUseCase } from "../domain/usecases/list_chat_sessions.ts"
import { CreateChatSessionUseCase } from "../domain/usecases/create_chat_session.ts"
import { ListChatMessagesUseCase } from "../domain/usecases/list_chat_messages.ts"
import { ListLearningPathsUseCase } from "../domain/usecases/list_learning_paths.ts"
import { CreateLearningPathUseCase } from "../domain/usecases/create_learning_path.ts"
import { GetUserSettingsUseCase } from "../domain/usecases/get_user_settings.ts"
import { UpdateUserSettingsUseCase } from "../domain/usecases/update_user_settings.ts"
import type { UserRepositoryPort } from "../domain/ports/user_repository.ts"
import type { PasswordHasherPort, TokenIssuerPort } from "../domain/ports/auth.ts"
import type { ChatSessionRepositoryPort } from "../domain/ports/chat_session_repository.ts"
import type { LearningPathRepositoryPort } from "../domain/ports/learning_path_repository.ts"
import type { UserSettingsRepositoryPort } from "../domain/ports/user_settings_repository.ts"

export type Container = {
  // Infrastructure
  searchCoursesUseCase: SearchCoursesUseCase
  chatUseCase: ChatUseCase
  userRepository: UserRepositoryPort
  passwordHasher: PasswordHasherPort
  tokenIssuer: TokenIssuerPort
  // Auth
  registerUserUseCase: RegisterUserUseCase
  loginUserUseCase: LoginUserUseCase
  refreshTokenUseCase: RefreshTokenUseCase
  // Chat sessions
  chatSessionRepository: ChatSessionRepositoryPort
  listChatSessionsUseCase: ListChatSessionsUseCase
  createChatSessionUseCase: CreateChatSessionUseCase
  listChatMessagesUseCase: ListChatMessagesUseCase
  // Learning paths
  learningPathRepository: LearningPathRepositoryPort
  listLearningPathsUseCase: ListLearningPathsUseCase
  createLearningPathUseCase: CreateLearningPathUseCase
  // User settings
  userSettingsRepository: UserSettingsRepositoryPort
  getUserSettingsUseCase: GetUserSettingsUseCase
  updateUserSettingsUseCase: UpdateUserSettingsUseCase
}

export function createContainer(): Container {
  const aiProcessingClient = new AIProcessingClient()
  const userRepository = new DrizzleUserRepository()
  const passwordHasher = new BcryptPasswordHasher()
  const tokenIssuer = new JoseTokenIssuer()
  const chatSessionRepository = new DrizzleChatSessionRepository()
  const learningPathRepository = new DrizzleLearningPathRepository()
  const userSettingsRepository = new DrizzleUserSettingsRepository()

  return {
    // Infrastructure
    searchCoursesUseCase: new SearchCoursesUseCase(aiProcessingClient),
    chatUseCase: new ChatUseCase(aiProcessingClient, chatSessionRepository),
    userRepository,
    passwordHasher,
    tokenIssuer,
    // Auth
    registerUserUseCase: new RegisterUserUseCase(userRepository, passwordHasher, tokenIssuer),
    loginUserUseCase: new LoginUserUseCase(userRepository, passwordHasher, tokenIssuer),
    refreshTokenUseCase: new RefreshTokenUseCase(tokenIssuer),
    // Chat sessions
    chatSessionRepository,
    listChatSessionsUseCase: new ListChatSessionsUseCase(chatSessionRepository),
    createChatSessionUseCase: new CreateChatSessionUseCase(chatSessionRepository),
    listChatMessagesUseCase: new ListChatMessagesUseCase(chatSessionRepository),
    // Learning paths
    learningPathRepository,
    listLearningPathsUseCase: new ListLearningPathsUseCase(learningPathRepository),
    createLearningPathUseCase: new CreateLearningPathUseCase(learningPathRepository),
    // User settings
    userSettingsRepository,
    getUserSettingsUseCase: new GetUserSettingsUseCase(userSettingsRepository),
    updateUserSettingsUseCase: new UpdateUserSettingsUseCase(userSettingsRepository),
  }
}

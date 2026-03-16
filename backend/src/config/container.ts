import { AIProcessingClient } from "../infrastructure/llm/ai_processing_client.ts"
import { SearchCoursesUseCase } from "../domain/usecases/search_courses.ts"
import { ChatUseCase } from "../domain/usecases/chat.ts"
import { DrizzleUserRepository } from "../infrastructure/db/user_repository.ts"
import { RegisterUserUseCase } from "../domain/usecases/register_user.ts"
import { LoginUserUseCase } from "../domain/usecases/login_user.ts"
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
import type { ChatSessionRepositoryPort } from "../domain/ports/chat_session_repository.ts"
import type { LearningPathRepositoryPort } from "../domain/ports/learning_path_repository.ts"
import type { UserSettingsRepositoryPort } from "../domain/ports/user_settings_repository.ts"

export type Container = {
  // Existing
  searchCoursesUseCase: SearchCoursesUseCase
  chatUseCase: ChatUseCase
  userRepository: UserRepositoryPort
  registerUserUseCase: RegisterUserUseCase
  loginUserUseCase: LoginUserUseCase
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
  const chatSessionRepository = new DrizzleChatSessionRepository()
  const learningPathRepository = new DrizzleLearningPathRepository()
  const userSettingsRepository = new DrizzleUserSettingsRepository()

  return {
    // Existing
    searchCoursesUseCase: new SearchCoursesUseCase(aiProcessingClient),
    chatUseCase: new ChatUseCase(aiProcessingClient),
    userRepository,
    registerUserUseCase: new RegisterUserUseCase(userRepository),
    loginUserUseCase: new LoginUserUseCase(userRepository),
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

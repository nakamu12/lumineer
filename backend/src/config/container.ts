import { AIProcessingClient } from "../infrastructure/llm/ai_processing_client.ts";
import { SearchCoursesUseCase } from "../domain/usecases/search_courses.ts";
import { ChatUseCase } from "../domain/usecases/chat.ts";
import { DrizzleUserRepository } from "../infrastructure/db/user_repository.ts";
import { RegisterUserUseCase } from "../domain/usecases/register_user.ts";
import { LoginUserUseCase } from "../domain/usecases/login_user.ts";
import type { UserRepositoryPort } from "../domain/ports/user_repository.ts";

export type Container = {
  searchCoursesUseCase: SearchCoursesUseCase;
  chatUseCase: ChatUseCase;
  userRepository: UserRepositoryPort;
  registerUserUseCase: RegisterUserUseCase;
  loginUserUseCase: LoginUserUseCase;
};

export function createContainer(): Container {
  const aiProcessingClient = new AIProcessingClient();
  const userRepository = new DrizzleUserRepository();

  return {
    searchCoursesUseCase: new SearchCoursesUseCase(aiProcessingClient),
    chatUseCase: new ChatUseCase(aiProcessingClient),
    userRepository,
    registerUserUseCase: new RegisterUserUseCase(userRepository),
    loginUserUseCase: new LoginUserUseCase(userRepository),
  };
}

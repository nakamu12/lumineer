import { AIProcessingClient } from "../infrastructure/llm/ai_processing_client.ts"
import { SearchCoursesUseCase } from "../domain/usecases/search_courses.ts"
import { ChatUseCase } from "../domain/usecases/chat.ts"
import { DrizzleUserRepository } from "../infrastructure/db/user_repository.ts"
import { BcryptPasswordHasher } from "../infrastructure/auth/password.ts"
import { JoseTokenIssuer } from "../infrastructure/auth/jwt.ts"
import { RegisterUserUseCase } from "../domain/usecases/register_user.ts"
import { LoginUserUseCase } from "../domain/usecases/login_user.ts"
import { RefreshTokenUseCase } from "../domain/usecases/refresh_token.ts"
import type { UserRepositoryPort } from "../domain/ports/user_repository.ts"
import type { PasswordHasherPort, TokenIssuerPort } from "../domain/ports/auth.ts"

export type Container = {
  searchCoursesUseCase: SearchCoursesUseCase
  chatUseCase: ChatUseCase
  userRepository: UserRepositoryPort
  passwordHasher: PasswordHasherPort
  tokenIssuer: TokenIssuerPort
  registerUserUseCase: RegisterUserUseCase
  loginUserUseCase: LoginUserUseCase
  refreshTokenUseCase: RefreshTokenUseCase
}

export function createContainer(): Container {
  const aiProcessingClient = new AIProcessingClient()
  const userRepository = new DrizzleUserRepository()
  const passwordHasher = new BcryptPasswordHasher()
  const tokenIssuer = new JoseTokenIssuer()

  return {
    searchCoursesUseCase: new SearchCoursesUseCase(aiProcessingClient),
    chatUseCase: new ChatUseCase(aiProcessingClient),
    userRepository,
    passwordHasher,
    tokenIssuer,
    registerUserUseCase: new RegisterUserUseCase(userRepository, passwordHasher, tokenIssuer),
    loginUserUseCase: new LoginUserUseCase(userRepository, passwordHasher, tokenIssuer),
    refreshTokenUseCase: new RefreshTokenUseCase(tokenIssuer),
  }
}

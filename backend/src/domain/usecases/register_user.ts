import type { UserRepositoryPort } from "../ports/user_repository.ts"
import type { UserEntity } from "../entities/user.ts"
import { hashPassword } from "../../infrastructure/auth/password.ts"
import { issueTokenPair, type TokenPair } from "../../infrastructure/auth/jwt.ts"
import { ConflictError } from "../errors.ts"

export type RegisterUserInput = {
  email: string
  password: string
  displayName: string
}

export type RegisterUserResult = {
  user: UserEntity
  tokens: TokenPair
}

export class RegisterUserUseCase {
  constructor(private readonly userRepository: UserRepositoryPort) {}

  async execute(input: RegisterUserInput): Promise<RegisterUserResult> {
    const exists = await this.userRepository.existsByEmail(input.email)
    if (exists) {
      throw new ConflictError("Email already registered")
    }

    const passwordHash = await hashPassword(input.password)
    const user = await this.userRepository.create({
      email: input.email,
      passwordHash,
      displayName: input.displayName,
    })

    const tokens = await issueTokenPair(user.id)
    return { user, tokens }
  }
}

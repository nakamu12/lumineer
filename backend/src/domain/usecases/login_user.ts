import type { UserRepositoryPort } from "../ports/user_repository.ts"
import type { UserEntity } from "../entities/user.ts"
import { verifyPassword } from "../../infrastructure/auth/password.ts"
import { issueTokenPair, type TokenPair } from "../../infrastructure/auth/jwt.ts"
import { UnauthorizedError } from "../errors.ts"

export type LoginUserInput = {
  email: string
  password: string
}

export type LoginUserResult = {
  user: UserEntity
  tokens: TokenPair
}

export class LoginUserUseCase {
  constructor(private readonly userRepository: UserRepositoryPort) {}

  async execute(input: LoginUserInput): Promise<LoginUserResult> {
    const userWithHash = await this.userRepository.findByEmail(input.email)
    if (!userWithHash) {
      throw new UnauthorizedError("Invalid email or password")
    }

    const valid = await verifyPassword(input.password, userWithHash.passwordHash)
    if (!valid) {
      throw new UnauthorizedError("Invalid email or password")
    }

    const { passwordHash: _, ...user } = userWithHash
    const tokens = await issueTokenPair(user.id)
    return { user, tokens }
  }
}

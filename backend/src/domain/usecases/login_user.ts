import type { UserRepositoryPort } from "../ports/user_repository.ts"
import type { UserEntity } from "../entities/user.ts"
import type { PasswordHasherPort, TokenIssuerPort, TokenPair } from "../ports/auth.ts"
import { AuthenticationError } from "../errors.ts"

export type LoginUserInput = {
  email: string
  password: string
}

export type LoginUserResult = {
  user: UserEntity
  tokens: TokenPair
}

export class LoginUserUseCase {
  constructor(
    private readonly userRepository: UserRepositoryPort,
    private readonly passwordHasher: PasswordHasherPort,
    private readonly tokenIssuer: TokenIssuerPort,
  ) {}

  async execute(input: LoginUserInput): Promise<LoginUserResult> {
    const userWithHash = await this.userRepository.findByEmail(input.email)
    if (!userWithHash) {
      throw new AuthenticationError("Invalid email or password")
    }

    const valid = await this.passwordHasher.verify(input.password, userWithHash.passwordHash)
    if (!valid) {
      throw new AuthenticationError("Invalid email or password")
    }

    const { passwordHash: _, ...user } = userWithHash
    const tokens = await this.tokenIssuer.issueTokenPair(user.id)
    return { user, tokens }
  }
}

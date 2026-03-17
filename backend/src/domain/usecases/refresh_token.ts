import type { TokenIssuerPort } from "../ports/auth.ts"
import { AuthenticationError } from "../errors.ts"

export type RefreshTokenResult = {
  accessToken: string
}

export class RefreshTokenUseCase {
  constructor(private readonly tokenIssuer: TokenIssuerPort) {}

  async execute(refreshToken: string): Promise<RefreshTokenResult> {
    const payload = await this.tokenIssuer.verifyToken(refreshToken).catch(() => {
      throw new AuthenticationError("Invalid or expired refresh token")
    })

    if (payload.type !== "refresh") {
      throw new AuthenticationError("Invalid token type")
    }

    const accessToken = await this.tokenIssuer.issueAccessToken(payload.sub)
    return { accessToken }
  }
}

import { SignJWT, jwtVerify } from "jose"
import { getSettings } from "../../config/settings.ts"
import type {
  TokenIssuerPort,
  TokenPair,
  TokenPayload,
  TokenType,
} from "../../domain/ports/auth.ts"

function getSecret(): Uint8Array {
  const { JWT_SECRET } = getSettings()
  return new TextEncoder().encode(JWT_SECRET)
}

export class JoseTokenIssuer implements TokenIssuerPort {
  async issueAccessToken(userId: string): Promise<string> {
    return this.signToken(userId, "access")
  }

  private async signToken(userId: string, type: TokenType): Promise<string> {
    const { JWT_ACCESS_EXPIRES, JWT_REFRESH_EXPIRES } = getSettings()
    const expiresIn = type === "access" ? JWT_ACCESS_EXPIRES : JWT_REFRESH_EXPIRES

    return new SignJWT({ type })
      .setProtectedHeader({ alg: "HS256" })
      .setSubject(userId)
      .setIssuedAt()
      .setExpirationTime(expiresIn)
      .sign(getSecret())
  }

  async verifyToken(token: string): Promise<TokenPayload> {
    const { payload } = await jwtVerify(token, getSecret())
    if (
      typeof payload.sub !== "string" ||
      (payload["type"] !== "access" && payload["type"] !== "refresh")
    ) {
      throw new Error("Invalid token payload")
    }
    return { sub: payload.sub, type: payload["type"] as TokenType }
  }

  async issueTokenPair(userId: string): Promise<TokenPair> {
    const [accessToken, refreshToken] = await Promise.all([
      this.signToken(userId, "access"),
      this.signToken(userId, "refresh"),
    ])
    return { accessToken, refreshToken }
  }
}

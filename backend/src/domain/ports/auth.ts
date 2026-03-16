export type TokenPair = {
  accessToken: string
  refreshToken: string
}

export type TokenType = "access" | "refresh"

export type TokenPayload = {
  sub: string
  type: TokenType
}

export interface PasswordHasherPort {
  hash(plaintext: string): Promise<string>
  verify(plaintext: string, hash: string): Promise<boolean>
}

export interface TokenIssuerPort {
  issueTokenPair(userId: string): Promise<TokenPair>
  signToken(userId: string, type: TokenType): Promise<string>
  verifyToken(token: string): Promise<TokenPayload>
}

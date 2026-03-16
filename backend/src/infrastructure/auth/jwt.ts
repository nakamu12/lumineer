import { SignJWT, jwtVerify } from "jose";
import { getSettings } from "../../config/settings.ts";

export type TokenType = "access" | "refresh";

export type JwtPayload = {
  sub: string;
  type: TokenType;
};

function getSecret(): Uint8Array {
  const { JWT_SECRET } = getSettings();
  return new TextEncoder().encode(JWT_SECRET);
}

export async function signToken(
  userId: string,
  type: TokenType
): Promise<string> {
  const { JWT_ACCESS_EXPIRES, JWT_REFRESH_EXPIRES } = getSettings();
  const expiresIn = type === "access" ? JWT_ACCESS_EXPIRES : JWT_REFRESH_EXPIRES;

  return new SignJWT({ type })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(userId)
    .setIssuedAt()
    .setExpirationTime(expiresIn)
    .sign(getSecret());
}

export async function verifyToken(token: string): Promise<JwtPayload> {
  const { payload } = await jwtVerify(token, getSecret());
  if (
    typeof payload.sub !== "string" ||
    (payload["type"] !== "access" && payload["type"] !== "refresh")
  ) {
    throw new Error("Invalid token payload");
  }
  return { sub: payload.sub, type: payload["type"] as TokenType };
}

export type TokenPair = {
  accessToken: string;
  refreshToken: string;
};

export async function issueTokenPair(userId: string): Promise<TokenPair> {
  const [accessToken, refreshToken] = await Promise.all([
    signToken(userId, "access"),
    signToken(userId, "refresh"),
  ]);
  return { accessToken, refreshToken };
}

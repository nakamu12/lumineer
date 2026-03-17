import bcrypt from "bcryptjs"
import type { PasswordHasherPort } from "../../domain/ports/auth.ts"

const SALT_ROUNDS = 12

export class BcryptPasswordHasher implements PasswordHasherPort {
  async hash(plaintext: string): Promise<string> {
    return bcrypt.hash(plaintext, SALT_ROUNDS)
  }

  async verify(plaintext: string, hash: string): Promise<boolean> {
    return bcrypt.compare(plaintext, hash)
  }
}

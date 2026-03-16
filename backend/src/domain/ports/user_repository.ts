import type { UserEntity, UserEntityWithHash } from "../entities/user.ts"

export type CreateUserInput = {
  email: string
  passwordHash: string
  displayName: string
}

export interface UserRepositoryPort {
  findById(id: string): Promise<UserEntity | null>
  findByEmail(email: string): Promise<UserEntityWithHash | null>
  create(input: CreateUserInput): Promise<UserEntity>
  existsByEmail(email: string): Promise<boolean>
}

import { eq } from "drizzle-orm"
import type { UserRepositoryPort, CreateUserInput } from "../../domain/ports/user_repository.ts"
import type { UserEntity, UserEntityWithHash } from "../../domain/entities/user.ts"
import { UserFactory } from "../../domain/entities/user.ts"
import { getDb } from "./client.ts"
import { users } from "./schema.ts"

export class DrizzleUserRepository implements UserRepositoryPort {
  async findById(id: string): Promise<UserEntity | null> {
    const db = getDb()
    const rows = await db.select().from(users).where(eq(users.id, id)).limit(1)
    const row = rows[0]
    if (!row) return null
    return UserFactory.create({
      id: row.id,
      email: row.email,
      displayName: row.displayName,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    })
  }

  async findByEmail(email: string): Promise<UserEntityWithHash | null> {
    const db = getDb()
    const rows = await db
      .select()
      .from(users)
      .where(eq(users.email, email.toLowerCase().trim()))
      .limit(1)
    const row = rows[0]
    if (!row) return null
    return UserFactory.createWithHash({
      id: row.id,
      email: row.email,
      displayName: row.displayName,
      passwordHash: row.passwordHash,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    })
  }

  async create(input: CreateUserInput): Promise<UserEntity> {
    const db = getDb()
    const rows = await db
      .insert(users)
      .values({
        email: input.email.toLowerCase().trim(),
        passwordHash: input.passwordHash,
        displayName: input.displayName.trim(),
      })
      .returning()
    const row = rows[0]
    if (!row) throw new Error("Failed to create user")
    return UserFactory.create({
      id: row.id,
      email: row.email,
      displayName: row.displayName,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    })
  }

  async existsByEmail(email: string): Promise<boolean> {
    const db = getDb()
    const rows = await db
      .select({ id: users.id })
      .from(users)
      .where(eq(users.email, email.toLowerCase().trim()))
      .limit(1)
    return rows.length > 0
  }
}

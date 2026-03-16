export type UserEntity = {
  id: string
  email: string
  displayName: string
  createdAt: Date
  updatedAt: Date
}

export type UserEntityWithHash = UserEntity & {
  passwordHash: string
}

type CreateUserParams = {
  id: string
  email: string
  displayName: string
  createdAt: Date
  updatedAt: Date
}

type CreateUserWithHashParams = CreateUserParams & {
  passwordHash: string
}

export const UserFactory = {
  create(params: CreateUserParams): UserEntity {
    if (!params.email || !params.email.includes("@")) {
      throw new Error("Invalid email address")
    }
    if (!params.displayName || params.displayName.trim().length === 0) {
      throw new Error("Display name cannot be empty")
    }
    return {
      id: params.id,
      email: params.email.toLowerCase().trim(),
      displayName: params.displayName.trim(),
      createdAt: params.createdAt,
      updatedAt: params.updatedAt,
    }
  },

  createWithHash(params: CreateUserWithHashParams): UserEntityWithHash {
    const base = UserFactory.create(params)
    return { ...base, passwordHash: params.passwordHash }
  },
}

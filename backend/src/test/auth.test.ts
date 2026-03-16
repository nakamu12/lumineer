import { describe, it, expect, beforeEach } from "vitest"
import { createRouter } from "../interfaces/api/routes.ts"
import type { Container } from "../config/container.ts"
import type { UserRepositoryPort, CreateUserInput } from "../domain/ports/user_repository.ts"
import type { UserEntity, UserEntityWithHash } from "../domain/entities/user.ts"
import { UserFactory } from "../domain/entities/user.ts"
import { RegisterUserUseCase } from "../domain/usecases/register_user.ts"
import { LoginUserUseCase } from "../domain/usecases/login_user.ts"
import { verifyToken } from "../infrastructure/auth/jwt.ts"

// ── In-memory user repository ────────────────────────────────────────────────

class InMemoryUserRepository implements UserRepositoryPort {
  private users: Map<string, UserEntityWithHash> = new Map()
  private nextId = 1

  async findById(id: string): Promise<UserEntity | null> {
    const user = this.users.get(id)
    if (!user) return null
    const { passwordHash: _, ...rest } = user
    return rest
  }

  async findByEmail(email: string): Promise<UserEntityWithHash | null> {
    const normalized = email.toLowerCase().trim()
    for (const user of this.users.values()) {
      if (user.email === normalized) return user
    }
    return null
  }

  async create(input: CreateUserInput): Promise<UserEntity> {
    const id = `test-user-${this.nextId++}`
    const now = new Date()
    const entity = UserFactory.createWithHash({
      id,
      email: input.email.toLowerCase().trim(),
      displayName: input.displayName.trim(),
      passwordHash: input.passwordHash,
      createdAt: now,
      updatedAt: now,
    })
    this.users.set(id, entity)
    const { passwordHash: _, ...rest } = entity
    return rest
  }

  async existsByEmail(email: string): Promise<boolean> {
    const normalized = email.toLowerCase().trim()
    for (const user of this.users.values()) {
      if (user.email === normalized) return true
    }
    return false
  }

  clear(): void {
    this.users.clear()
    this.nextId = 1
  }
}

// ── Test helpers ─────────────────────────────────────────────────────────────

function createTestContainer(userRepository: InMemoryUserRepository): Container {
  return {
    searchCoursesUseCase: { execute: () => Promise.reject(new Error("not implemented")) } as never,
    chatUseCase: { execute: () => Promise.reject(new Error("not implemented")) } as never,
    userRepository,
    registerUserUseCase: new RegisterUserUseCase(userRepository),
    loginUserUseCase: new LoginUserUseCase(userRepository),
  }
}

function json(body: Record<string, unknown>): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("Auth API", () => {
  let repo: InMemoryUserRepository
  let app: ReturnType<typeof createRouter>

  beforeEach(() => {
    repo = new InMemoryUserRepository()
    const container = createTestContainer(repo)
    app = createRouter(container)
  })

  // ── Register ───────────────────────────────────────────────────────────────

  describe("POST /api/auth/register", () => {
    it("registers a new user and returns tokens", async () => {
      const res = await app.request(
        "/api/auth/register",
        json({ email: "alice@example.com", password: "Password1", display_name: "Alice" }),
      )
      expect(res.status).toBe(201)

      const body = await res.json()
      expect(body.user.email).toBe("alice@example.com")
      expect(body.user.display_name).toBe("Alice")
      expect(body.user.id).toBeDefined()
      expect(body.access_token).toBeDefined()
      expect(body.refresh_token).toBeDefined()

      // Verify tokens are valid JWTs
      const accessPayload = await verifyToken(body.access_token)
      expect(accessPayload.type).toBe("access")
      expect(accessPayload.sub).toBe(body.user.id)

      const refreshPayload = await verifyToken(body.refresh_token)
      expect(refreshPayload.type).toBe("refresh")
    })

    it("returns 409 for duplicate email", async () => {
      await app.request(
        "/api/auth/register",
        json({ email: "alice@example.com", password: "Password1", display_name: "Alice" }),
      )

      const res = await app.request(
        "/api/auth/register",
        json({ email: "alice@example.com", password: "Password2", display_name: "Alice2" }),
      )
      expect(res.status).toBe(409)

      const body = await res.json()
      expect(body.error).toBe("Email already registered")
    })

    it("returns 400 for invalid email", async () => {
      const res = await app.request(
        "/api/auth/register",
        json({ email: "not-an-email", password: "Password1", display_name: "Alice" }),
      )
      expect(res.status).toBe(400)
    })

    it("returns 400 for short password", async () => {
      const res = await app.request(
        "/api/auth/register",
        json({ email: "alice@example.com", password: "Ab1", display_name: "Alice" }),
      )
      expect(res.status).toBe(400)
    })

    it("returns 400 for password without uppercase", async () => {
      const res = await app.request(
        "/api/auth/register",
        json({ email: "alice@example.com", password: "password1", display_name: "Alice" }),
      )
      expect(res.status).toBe(400)
    })

    it("returns 400 for password without lowercase", async () => {
      const res = await app.request(
        "/api/auth/register",
        json({ email: "alice@example.com", password: "PASSWORD1", display_name: "Alice" }),
      )
      expect(res.status).toBe(400)
    })

    it("returns 400 for password without number", async () => {
      const res = await app.request(
        "/api/auth/register",
        json({ email: "alice@example.com", password: "Password", display_name: "Alice" }),
      )
      expect(res.status).toBe(400)
    })

    it("returns 400 for empty display_name", async () => {
      const res = await app.request(
        "/api/auth/register",
        json({ email: "alice@example.com", password: "Password1", display_name: "" }),
      )
      expect(res.status).toBe(400)
    })

    it("returns 400 for missing fields", async () => {
      const res = await app.request("/api/auth/register", json({ email: "alice@example.com" }))
      expect(res.status).toBe(400)
    })
  })

  // ── Login ──────────────────────────────────────────────────────────────────

  describe("POST /api/auth/login", () => {
    beforeEach(async () => {
      await app.request(
        "/api/auth/register",
        json({ email: "alice@example.com", password: "Password1", display_name: "Alice" }),
      )
    })

    it("logs in with valid credentials", async () => {
      const res = await app.request(
        "/api/auth/login",
        json({ email: "alice@example.com", password: "Password1" }),
      )
      expect(res.status).toBe(200)

      const body = await res.json()
      expect(body.user.email).toBe("alice@example.com")
      expect(body.access_token).toBeDefined()
      expect(body.refresh_token).toBeDefined()
    })

    it("returns 401 for wrong password", async () => {
      const res = await app.request(
        "/api/auth/login",
        json({ email: "alice@example.com", password: "WrongPass1" }),
      )
      expect(res.status).toBe(401)

      const body = await res.json()
      expect(body.error).toBe("Invalid email or password")
    })

    it("returns 401 for non-existent email", async () => {
      const res = await app.request(
        "/api/auth/login",
        json({ email: "nobody@example.com", password: "Password1" }),
      )
      expect(res.status).toBe(401)
    })

    it("returns 400 for missing password", async () => {
      const res = await app.request("/api/auth/login", json({ email: "alice@example.com" }))
      expect(res.status).toBe(400)
    })
  })

  // ── Refresh ────────────────────────────────────────────────────────────────

  describe("POST /api/auth/refresh", () => {
    let refreshToken: string

    beforeEach(async () => {
      const res = await app.request(
        "/api/auth/register",
        json({ email: "alice@example.com", password: "Password1", display_name: "Alice" }),
      )
      const body = await res.json()
      refreshToken = body.refresh_token
    })

    it("issues a new access token with valid refresh token", async () => {
      const res = await app.request("/api/auth/refresh", json({ refresh_token: refreshToken }))
      expect(res.status).toBe(200)

      const body = await res.json()
      expect(body.access_token).toBeDefined()

      const payload = await verifyToken(body.access_token)
      expect(payload.type).toBe("access")
    })

    it("returns 401 for invalid refresh token", async () => {
      const res = await app.request("/api/auth/refresh", json({ refresh_token: "invalid-token" }))
      expect(res.status).toBe(401)
    })

    it("returns 401 when access token is used as refresh token", async () => {
      const loginRes = await app.request(
        "/api/auth/login",
        json({ email: "alice@example.com", password: "Password1" }),
      )
      const { access_token } = await loginRes.json()

      const res = await app.request("/api/auth/refresh", json({ refresh_token: access_token }))
      expect(res.status).toBe(401)
    })

    it("returns 400 for missing refresh_token", async () => {
      const res = await app.request("/api/auth/refresh", json({}))
      expect(res.status).toBe(400)
    })
  })

  // ── Me ─────────────────────────────────────────────────────────────────────

  describe("GET /api/auth/me", () => {
    let accessToken: string

    beforeEach(async () => {
      const res = await app.request(
        "/api/auth/register",
        json({ email: "alice@example.com", password: "Password1", display_name: "Alice" }),
      )
      const body = await res.json()
      accessToken = body.access_token
    })

    it("returns current user info with valid access token", async () => {
      const res = await app.request("/api/auth/me", {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      expect(res.status).toBe(200)

      const body = await res.json()
      expect(body.email).toBe("alice@example.com")
      expect(body.display_name).toBe("Alice")
      expect(body.id).toBeDefined()
      expect(body.created_at).toBeDefined()
    })

    it("returns 401 without authorization header", async () => {
      const res = await app.request("/api/auth/me")
      expect(res.status).toBe(401)
    })

    it("returns 401 with invalid token", async () => {
      const res = await app.request("/api/auth/me", {
        headers: { Authorization: "Bearer invalid-token" },
      })
      expect(res.status).toBe(401)
    })

    it("returns 401 when refresh token is used instead of access token", async () => {
      const loginRes = await app.request(
        "/api/auth/login",
        json({ email: "alice@example.com", password: "Password1" }),
      )
      const { refresh_token } = await loginRes.json()

      const res = await app.request("/api/auth/me", {
        headers: { Authorization: `Bearer ${refresh_token}` },
      })
      expect(res.status).toBe(401)
    })
  })
})

import { z } from "@hono/zod-openapi"

export const RegisterRequestSchema = z
  .object({
    email: z.string().email().openapi({ example: "user@example.com" }),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[0-9]/, "Password must contain at least one number")
      .openapi({ example: "MySecret42" }),
    display_name: z.string().min(1).max(100).openapi({ example: "Alice" }),
  })
  .openapi("RegisterRequest")

export const LoginRequestSchema = z
  .object({
    email: z.string().email().openapi({ example: "user@example.com" }),
    password: z.string().min(1).openapi({ example: "password123" }),
  })
  .openapi("LoginRequest")

export const RefreshRequestSchema = z
  .object({
    refresh_token: z.string().min(1).openapi({ example: "eyJhbGciOiJIUzI1NiJ9..." }),
  })
  .openapi("RefreshRequest")

export const AuthResponseSchema = z
  .object({
    user: z.object({
      id: z.string(),
      email: z.string(),
      display_name: z.string(),
    }),
    access_token: z.string(),
    refresh_token: z.string(),
  })
  .openapi("AuthResponse")

export const RefreshResponseSchema = z
  .object({
    access_token: z.string(),
  })
  .openapi("RefreshResponse")

export const MeResponseSchema = z
  .object({
    id: z.string(),
    email: z.string(),
    display_name: z.string(),
    created_at: z.string(),
  })
  .openapi("MeResponse")

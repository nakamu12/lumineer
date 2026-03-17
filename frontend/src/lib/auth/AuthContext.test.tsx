import { describe, it, expect, beforeEach, vi } from "vitest"
import { renderHook, act, waitFor } from "@testing-library/react"
import { AuthProvider, useAuth } from "./AuthContext"
import { clearTokens, setRefreshToken, getAccessToken, getRefreshToken } from "./token-store"
import type { ReactNode } from "react"

function createWrapper() {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <AuthProvider>{children}</AuthProvider>
  }
}

const mockUser = {
  id: "user-1",
  email: "test@example.com",
  display_name: "Test User",
}

const mockAuthResponse = {
  user: mockUser,
  access_token: "access-123",
  refresh_token: "refresh-456",
}

describe("AuthContext", () => {
  beforeEach(() => {
    clearTokens()
    vi.restoreAllMocks()
  })

  it("throws when useAuth is used outside AuthProvider", () => {
    expect(() => {
      renderHook(() => useAuth())
    }).toThrow("useAuth must be used within AuthProvider")
  })

  it("initializes with no user and finishes loading when no refresh token", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })

  describe("login", () => {
    it("sets user and tokens on successful login", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify(mockAuthResponse), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await act(async () => {
        await result.current.login("test@example.com", "Password1")
      })

      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
      expect(getAccessToken()).toBe("access-123")
      expect(getRefreshToken()).toBe("refresh-456")
    })

    it("throws error on login failure", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify({ error: "Invalid credentials" }), { status: 401 }),
      )

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await expect(
        act(async () => {
          await result.current.login("bad@example.com", "wrong")
        }),
      ).rejects.toThrow("Invalid credentials")

      expect(result.current.user).toBeNull()
    })
  })

  describe("register", () => {
    it("sets user and tokens on successful registration", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify(mockAuthResponse), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        }),
      )

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await act(async () => {
        await result.current.register("test@example.com", "Password1", "Test User")
      })

      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })

    it("throws error on registration failure", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify({ error: "Email already registered" }), { status: 409 }),
      )

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await expect(
        act(async () => {
          await result.current.register("taken@example.com", "Password1", "User")
        }),
      ).rejects.toThrow("Email already registered")
    })
  })

  describe("logout", () => {
    it("clears user and tokens", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify(mockAuthResponse), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await act(async () => {
        await result.current.login("test@example.com", "Password1")
      })

      expect(result.current.isAuthenticated).toBe(true)

      act(() => {
        result.current.logout()
      })

      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
      expect(getAccessToken()).toBeNull()
      expect(getRefreshToken()).toBeNull()
    })
  })

  describe("session restore", () => {
    it("restores user from refresh token on mount", async () => {
      setRefreshToken("stored-refresh")

      const fetchSpy = vi.spyOn(globalThis, "fetch")

      // First call: refresh token
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify({ access_token: "restored-access" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )

      // Second call: GET /api/auth/me
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify(mockUser), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })

    it("clears tokens when refresh fails on mount", async () => {
      setRefreshToken("expired-refresh")

      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify({ error: "Invalid" }), { status: 401 }),
      )

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
    })
  })
})

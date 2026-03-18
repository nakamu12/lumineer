import { describe, it, expect, beforeEach, vi } from "vitest"
import {
  getAccessToken,
  setAccessToken,
  getRefreshToken,
  setRefreshToken,
  clearTokens,
  getAuthHeaders,
  tryRefreshToken,
} from "./token-store"

describe("token-store", () => {
  beforeEach(() => {
    clearTokens()
    vi.restoreAllMocks()
  })

  describe("access token", () => {
    it("returns null when no token is set", () => {
      expect(getAccessToken()).toBeNull()
    })

    it("stores and retrieves the access token", () => {
      setAccessToken("test-token")
      expect(getAccessToken()).toBe("test-token")
    })

    it("clears the access token when set to null", () => {
      setAccessToken("test-token")
      setAccessToken(null)
      expect(getAccessToken()).toBeNull()
    })
  })

  describe("refresh token", () => {
    it("returns null when no token is stored", () => {
      expect(getRefreshToken()).toBeNull()
    })

    it("stores and retrieves the refresh token from localStorage", () => {
      setRefreshToken("refresh-abc")
      expect(getRefreshToken()).toBe("refresh-abc")
      expect(localStorage.getItem("lumineer_refresh_token")).toBe("refresh-abc")
    })

    it("removes the refresh token when set to null", () => {
      setRefreshToken("refresh-abc")
      setRefreshToken(null)
      expect(getRefreshToken()).toBeNull()
      expect(localStorage.getItem("lumineer_refresh_token")).toBeNull()
    })
  })

  describe("clearTokens", () => {
    it("clears both access and refresh tokens", () => {
      setAccessToken("access-123")
      setRefreshToken("refresh-456")

      clearTokens()

      expect(getAccessToken()).toBeNull()
      expect(getRefreshToken()).toBeNull()
    })
  })

  describe("getAuthHeaders", () => {
    it("returns empty object when no access token", () => {
      expect(getAuthHeaders()).toEqual({})
    })

    it("returns Authorization header when access token exists", () => {
      setAccessToken("my-token")
      expect(getAuthHeaders()).toEqual({ Authorization: "Bearer my-token" })
    })
  })

  describe("tryRefreshToken", () => {
    it("returns null when no refresh token is stored", async () => {
      const result = await tryRefreshToken()
      expect(result).toBeNull()
    })

    it("refreshes access token on success", async () => {
      setRefreshToken("valid-refresh")

      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify({ access_token: "new-access" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )

      const result = await tryRefreshToken()

      expect(result).toBe("new-access")
      expect(getAccessToken()).toBe("new-access")
    })

    it("clears tokens on refresh failure", async () => {
      setRefreshToken("expired-refresh")
      setAccessToken("old-access")

      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify({ error: "Invalid refresh token" }), { status: 401 }),
      )

      const result = await tryRefreshToken()

      expect(result).toBeNull()
      expect(getAccessToken()).toBeNull()
      expect(getRefreshToken()).toBeNull()
    })

    it("clears tokens on network error", async () => {
      setRefreshToken("some-refresh")
      setAccessToken("some-access")

      vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Network error"))

      const result = await tryRefreshToken()

      expect(result).toBeNull()
      expect(getAccessToken()).toBeNull()
      expect(getRefreshToken()).toBeNull()
    })

    it("deduplicates concurrent refresh calls", async () => {
      setRefreshToken("valid-refresh")

      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ access_token: "deduped-token" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )

      const [r1, r2, r3] = await Promise.all([
        tryRefreshToken(),
        tryRefreshToken(),
        tryRefreshToken(),
      ])

      expect(r1).toBe("deduped-token")
      expect(r2).toBe("deduped-token")
      expect(r3).toBe("deduped-token")
      expect(fetchSpy).toHaveBeenCalledTimes(1)
    })
  })
})

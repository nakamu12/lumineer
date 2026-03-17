const REFRESH_TOKEN_KEY = "lumineer_refresh_token"

let accessToken: string | null = null
let refreshPromise: Promise<string | null> | null = null

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? ""

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token: string | null): void {
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
}

export function clearTokens(): void {
  accessToken = null
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function getAuthHeaders(): Record<string, string> {
  const token = getAccessToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * Try to refresh the access token using the stored refresh token.
 * Deduplicates concurrent refresh attempts.
 */
export function tryRefreshToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    const refreshToken = getRefreshToken()
    if (!refreshToken) return null

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (!res.ok) {
        clearTokens()
        return null
      }

      const data = (await res.json()) as { access_token: string }
      setAccessToken(data.access_token)
      return data.access_token
    } catch {
      clearTokens()
      return null
    }
  })().finally(() => {
    refreshPromise = null
  })

  return refreshPromise
}

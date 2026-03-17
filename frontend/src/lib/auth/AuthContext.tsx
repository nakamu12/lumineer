import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react"
import {
  setAccessToken,
  setRefreshToken,
  getRefreshToken,
  clearTokens,
  tryRefreshToken,
} from "./token-store"

const API_BASE_URL = import.meta.env.VITE_API_URL ?? ""

export interface AuthUser {
  id: string
  email: string
  display_name: string
  created_at?: string
}

interface AuthResponse {
  user: AuthUser
  access_token: string
  refresh_token: string
}

interface AuthContextValue {
  user: AuthUser | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Restore session from refresh token on mount
  useEffect(() => {
    const init = async () => {
      const refreshToken = getRefreshToken()
      if (!refreshToken) {
        setIsLoading(false)
        return
      }

      try {
        const newToken = await tryRefreshToken()
        if (!newToken) {
          setIsLoading(false)
          return
        }

        const meRes = await fetch(`${API_BASE_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${newToken}` },
        })

        if (meRes.ok) {
          const userData = (await meRes.json()) as AuthUser
          setUser(userData)
        } else {
          clearTokens()
        }
      } catch {
        clearTokens()
      } finally {
        setIsLoading(false)
      }
    }

    void init()
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })

    if (!res.ok) {
      const body = await res.json().catch(() => ({ error: "Login failed" }))
      throw new Error((body as { error?: string }).error ?? "Login failed")
    }

    const data = (await res.json()) as AuthResponse
    setAccessToken(data.access_token)
    setRefreshToken(data.refresh_token)
    setUser(data.user)
  }, [])

  const register = useCallback(async (email: string, password: string, displayName: string) => {
    const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, display_name: displayName }),
    })

    if (!res.ok) {
      const body = await res.json().catch(() => ({ error: "Registration failed" }))
      throw new Error((body as { error?: string }).error ?? "Registration failed")
    }

    const data = (await res.json()) as AuthResponse
    setAccessToken(data.access_token)
    setRefreshToken(data.refresh_token)
    setUser(data.user)
  }, [])

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

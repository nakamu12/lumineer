import { useState, useCallback } from "react"
import type { ApiError } from "@/lib/types/api"
import { getAuthHeaders, getRefreshToken, tryRefreshToken } from "@/lib/auth/token-store"

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:3001"

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: ApiError | null
}

interface UseApiReturn<T> extends UseApiState<T> {
  execute: (path: string, options?: RequestInit) => Promise<T | null>
  reset: () => void
}

export function useApi<T = unknown>(): UseApiReturn<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  })

  const execute = useCallback(async (path: string, options?: RequestInit): Promise<T | null> => {
    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const response = await fetch(`${API_BASE_URL}${path}`, {
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
          ...options?.headers,
        },
        ...options,
      })

      // Auto-refresh on 401 if we have a refresh token
      if (response.status === 401 && getRefreshToken()) {
        const newToken = await tryRefreshToken()
        if (newToken) {
          const retryRes = await fetch(`${API_BASE_URL}${path}`, {
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${newToken}`,
              ...options?.headers,
            },
            ...options,
          })

          if (retryRes.ok) {
            const data = (await retryRes.json()) as T
            setState({ data, loading: false, error: null })
            return data
          }
        }

        const error: ApiError = { message: "Session expired. Please sign in again.", code: "401" }
        setState({ data: null, loading: false, error })
        return null
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw {
          message: (errorData as { message?: string }).message ?? "Request failed",
          code: String(response.status),
        }
      }

      const data = (await response.json()) as T
      setState({ data, loading: false, error: null })
      return data
    } catch (err) {
      const error = err as ApiError
      setState({ data: null, loading: false, error })
      return null
    }
  }, [])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return { ...state, execute, reset }
}

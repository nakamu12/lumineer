import { useState, useCallback } from "react"
import type { ApiError } from "@/lib/types/api"
import {
  getAuthHeaders,
  getRefreshToken,
  tryRefreshToken,
  API_BASE_URL,
} from "@/lib/auth/token-store"

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
        const message = (errorData as { message?: string }).message ?? "Request failed"
        const error = new Error(message) as Error & { code?: string }
        error.code = String(response.status)
        throw error
      }

      const data = (await response.json()) as T
      setState({ data, loading: false, error: null })
      return data
    } catch (err) {
      const message = err instanceof Error ? err.message : "An unexpected error occurred"
      const code = (err as { code?: string }).code ?? "UNKNOWN"
      const error: ApiError = { message, code }
      setState({ data: null, loading: false, error })
      return null
    }
  }, [])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return { ...state, execute, reset }
}

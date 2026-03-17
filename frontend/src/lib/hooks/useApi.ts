import { useState, useCallback } from "react"
import type { ApiError } from "@/lib/types/api"

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:3000"

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
          ...options?.headers,
        },
        ...options,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw { message: errorData.message ?? "Request failed", code: String(response.status) }
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

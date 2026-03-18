import { useState, useEffect, useCallback, useRef } from "react"
import type { Course, CourseSearchResult } from "@/lib/types/course"
import { useDebounce } from "@/lib/hooks/useDebounce"
import type { ApiError } from "@/lib/types/api"
import { getAuthHeaders } from "@/lib/auth/token-store"

const API_BASE_URL = import.meta.env.VITE_API_URL ?? ""
const LIMIT = 12

interface UseCourseSearchParams {
  query: string
  level?: string
  minRating?: string
}

interface UseCourseSearchReturn {
  courses: Course[]
  total: number
  aiSummary: string | undefined
  isLoading: boolean
  error: ApiError | null
  offset: number
  hasMore: boolean
  loadMore: () => void
  reset: () => void
}

export function useCourseSearch({
  query,
  level,
  minRating,
}: UseCourseSearchParams): UseCourseSearchReturn {
  const debouncedQuery = useDebounce(query, 300)

  const [courses, setCourses] = useState<Course[]>([])
  const [total, setTotal] = useState(0)
  const [aiSummary, setAiSummary] = useState<string | undefined>(undefined)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [offset, setOffset] = useState(0)

  // Track the latest fetch to avoid race conditions
  const fetchIdRef = useRef(0)

  const fetchCourses = useCallback(
    async (currentOffset: number, append: boolean) => {
      if (!debouncedQuery.trim()) {
        setCourses([])
        setTotal(0)
        setAiSummary(undefined)
        setError(null)
        return
      }

      const fetchId = ++fetchIdRef.current
      setIsLoading(true)
      setError(null)

      try {
        const body: Record<string, unknown> = {
          query: debouncedQuery,
          limit: LIMIT,
        }
        if (level) body.level = level
        if (minRating) body.min_rating = Number(minRating)

        const response = await fetch(`${API_BASE_URL}/api/search`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...getAuthHeaders() },
          body: JSON.stringify(body),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw {
            message: (errorData as { message?: string }).message ?? "Search failed",
            code: String(response.status),
          } as ApiError
        }

        const data = (await response.json()) as CourseSearchResult

        // Ignore stale responses
        if (fetchId !== fetchIdRef.current) return

        if (append) {
          setCourses((prev) => [...prev, ...data.courses])
        } else {
          setCourses(data.courses)
        }
        setTotal(data.total ?? data.courses?.length ?? 0)
        setAiSummary(data.summary ?? data.ai_summary)
      } catch (err) {
        if (fetchId !== fetchIdRef.current) return
        setError(err as ApiError)
      } finally {
        if (fetchId === fetchIdRef.current) {
          setIsLoading(false)
        }
      }
    },
    [debouncedQuery, level, minRating],
  )

  // Reset and re-fetch when query or filters change
  useEffect(() => {
    setOffset(0)
    void fetchCourses(0, false)
  }, [fetchCourses])

  const loadMore = useCallback(() => {
    const newOffset = offset + LIMIT
    setOffset(newOffset)
    void fetchCourses(newOffset, true)
  }, [offset, fetchCourses])

  const reset = useCallback(() => {
    setCourses([])
    setTotal(0)
    setAiSummary(undefined)
    setError(null)
    setOffset(0)
  }, [])

  const hasMore = courses.length < total

  return {
    courses,
    total,
    aiSummary,
    isLoading,
    error,
    offset,
    hasMore,
    loadMore,
    reset,
  }
}

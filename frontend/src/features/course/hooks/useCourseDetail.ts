import { useState, useEffect, useCallback } from "react"
import type { Course } from "@/lib/types/course"
import type { ApiError } from "@/lib/types/api"

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:3001"

interface UseCourseDetailReturn {
  course: Course | null
  isLoading: boolean
  error: ApiError | null
}

export function useCourseDetail(
  courseId: string,
  initialCourse: Course | null,
): UseCourseDetailReturn {
  const [course, setCourse] = useState<Course | null>(initialCourse)
  const [isLoading, setIsLoading] = useState(!initialCourse)
  const [error, setError] = useState<ApiError | null>(null)

  const fetchCourse = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/courses/${encodeURIComponent(courseId)}`)

      if (response.status === 404) {
        setError({ message: "Course not found", code: "404" })
        setCourse(null)
        return
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw {
          message: (errorData as { error?: string }).error ?? "Failed to load course",
          code: String(response.status),
        } as ApiError
      }

      const data = (await response.json()) as Course
      setCourse(data)
    } catch (err) {
      if (err instanceof Error) {
        setError({ message: err.message })
      } else {
        setError(err as ApiError)
      }
    } finally {
      setIsLoading(false)
    }
  }, [courseId])

  useEffect(() => {
    if (!initialCourse) {
      void fetchCourse()
    }
  }, [initialCourse, fetchCourse])

  return { course, isLoading, error }
}

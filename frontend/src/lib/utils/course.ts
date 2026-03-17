import type { Course } from "@/lib/types/course"

export function getLevelBadgeClass(level: Course["level"]): string {
  switch (level) {
    case "Beginner":
      return "bg-green-100 text-green-800 border-green-200"
    case "Intermediate":
      return "bg-blue-100 text-blue-800 border-blue-200"
    case "Advanced":
      return "bg-orange-100 text-orange-800 border-orange-200"
    default:
      return "bg-gray-100 text-gray-600 border-gray-200"
  }
}

export function formatEnrolled(count: number): string {
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}k`
  return String(count)
}

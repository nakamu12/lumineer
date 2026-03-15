import { ExternalLink, Star } from "lucide-react"

import { Button } from "@/lib/ui/button"
import type { Course } from "@/lib/types/course"

const levelVariant: Record<string, string> = {
  Beginner: "bg-emerald-100 text-emerald-700",
  Intermediate: "bg-blue-100 text-blue-700",
  Advanced: "bg-orange-100 text-orange-700",
}

interface CourseCardMiniProps {
  course: Course
}

export function CourseCardMini({ course }: CourseCardMiniProps) {
  const formatEnrolled = (n: number) =>
    n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n)

  return (
    <div className="flex items-center gap-3 rounded-lg border bg-background p-3 hover:bg-muted/30 transition-colors">
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm leading-tight line-clamp-1">{course.title}</p>
        <p className="text-xs text-muted-foreground mt-0.5">{course.organization}</p>
        <div className="flex items-center gap-2 mt-1 flex-wrap">
          {course.level && (
            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${levelVariant[course.level] ?? "bg-gray-100 text-gray-700"}`}>
              {course.level}
            </span>
          )}
          <span className="flex items-center gap-0.5 text-xs text-amber-500">
            <Star className="h-3 w-3 fill-current" />
            {course.rating.toFixed(1)}
          </span>
          <span className="text-xs text-muted-foreground">{formatEnrolled(course.enrolled)} enrolled</span>
        </div>
      </div>
      <Button asChild variant="ghost" size="sm" className="shrink-0 h-7 px-2 text-xs">
        <a href={course.url} target="_blank" rel="noopener noreferrer">
          <ExternalLink className="h-3 w-3 mr-1" />
          View
        </a>
      </Button>
    </div>
  )
}

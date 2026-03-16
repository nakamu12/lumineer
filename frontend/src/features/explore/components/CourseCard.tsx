import { ExternalLink, Star, Users } from "lucide-react"
import { Card, CardContent, CardFooter, CardHeader } from "@/lib/ui/card"
import { Badge } from "@/lib/ui/badge"
import { Button } from "@/lib/ui/button"
import { cn } from "@/lib/utils"
import type { Course } from "@/lib/types/course"

interface CourseCardProps {
  course: Course
}

function formatEnrolled(count: number): string {
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}k`
  return String(count)
}

function getLevelBadgeClass(level: Course["level"]): string {
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

export function CourseCard({ course }: CourseCardProps) {
  const visibleSkills = course.skills.slice(0, 3)
  const remainingSkills = course.skills.length - 3

  return (
    <Card className="flex flex-col h-full transition-shadow hover:shadow-md hover:border-primary/30">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3
              className="font-semibold text-base leading-snug line-clamp-2 mb-1"
              title={course.title}
            >
              {course.title}
            </h3>
            <p className="text-sm text-muted-foreground truncate">{course.organization}</p>
          </div>
          {course.level && (
            <Badge
              variant="outline"
              className={cn("shrink-0 text-xs", getLevelBadgeClass(course.level))}
            >
              {course.level}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 pb-3">
        <div className="flex items-center gap-3 text-sm text-muted-foreground mb-3">
          <span className="flex items-center gap-1">
            <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
            <span className="font-medium text-foreground">{course.rating.toFixed(1)}</span>
          </span>
          <span className="flex items-center gap-1">
            <Users className="h-3.5 w-3.5" />
            <span>{formatEnrolled(course.enrolled)} enrolled</span>
          </span>
        </div>

        {visibleSkills.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {visibleSkills.map((skill) => (
              <Badge key={skill} variant="secondary" className="text-xs px-2 py-0.5">
                {skill}
              </Badge>
            ))}
            {remainingSkills > 0 && (
              <Badge variant="outline" className="text-xs px-2 py-0.5 text-muted-foreground">
                +{remainingSkills} more
              </Badge>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="pt-0">
        <Button variant="outline" size="sm" className="w-full gap-1.5" asChild>
          <a href={course.url} target="_blank" rel="noopener noreferrer">
            View Course
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </Button>
      </CardFooter>
    </Card>
  )
}

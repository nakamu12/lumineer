import { useParams, useLocation, Link } from "react-router-dom"
import { useState } from "react"
import {
  ArrowLeft,
  ExternalLink,
  Star,
  Users,
  GraduationCap,
  Building2,
  Clock,
  BookOpen,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  User,
} from "lucide-react"
import { Badge } from "@/lib/ui/badge"
import { Button } from "@/lib/ui/button"
import { Card, CardContent, CardHeader } from "@/lib/ui/card"
import { Separator } from "@/lib/ui/separator"
import { Skeleton } from "@/lib/ui/skeleton"
import { cn } from "@/lib/utils"
import type { Course } from "@/lib/types/course"
import { useCourseDetail } from "./hooks/useCourseDetail"

const DESCRIPTION_PREVIEW_LENGTH = 300

function getLevelColor(level: Course["level"]): string {
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

function formatEnrolled(count: number): string {
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}k`
  return String(count)
}

function CourseDetailSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <Skeleton className="h-8 w-48" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flex flex-col gap-6">
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
        <div className="flex flex-col gap-4">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </div>
    </div>
  )
}

export function CourseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const initialCourse = (location.state as { course?: Course } | null)?.course ?? null

  const { course, isLoading, error } = useCourseDetail(id ?? "", initialCourse)

  const [descriptionExpanded, setDescriptionExpanded] = useState(false)

  if (isLoading) {
    return <CourseDetailSkeleton />
  }

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <AlertCircle className="h-12 w-12 text-destructive opacity-50" />
        <h2 className="text-xl font-semibold">Course not found</h2>
        <p className="text-muted-foreground max-w-md">
          The course you&apos;re looking for doesn&apos;t exist or has been removed.
        </p>
        <Button asChild variant="outline">
          <Link to="/explore">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Explore
          </Link>
        </Button>
      </div>
    )
  }

  if (!course) {
    return null
  }

  const descriptionTruncated =
    course.description.length > DESCRIPTION_PREVIEW_LENGTH && !descriptionExpanded
  const displayDescription = descriptionTruncated
    ? course.description.slice(0, DESCRIPTION_PREVIEW_LENGTH) + "..."
    : course.description

  return (
    <div className="flex flex-col gap-6">
      {/* Back link */}
      <div>
        <Button asChild variant="ghost" size="sm" className="gap-1.5 -ml-2">
          <Link to="/explore">
            <ArrowLeft className="h-4 w-4" />
            Back to Explore
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content — left column */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Title & organization */}
          <div className="flex flex-col gap-2">
            <div className="flex items-start gap-3">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight leading-tight flex-1">
                {course.title}
              </h1>
              {course.level && (
                <Badge
                  variant="outline"
                  className={cn("shrink-0 text-sm mt-1", getLevelColor(course.level))}
                >
                  {course.level}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-4 text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Building2 className="h-4 w-4" />
                {course.organization}
              </span>
              {course.instructor && (
                <span className="flex items-center gap-1.5">
                  <User className="h-4 w-4" />
                  {course.instructor}
                </span>
              )}
            </div>
          </div>

          {/* Stats row */}
          <div className="flex items-center gap-6 text-sm">
            <span className="flex items-center gap-1.5">
              <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
              <span className="font-semibold text-lg">{course.rating.toFixed(1)}</span>
            </span>
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Users className="h-4 w-4" />
              {formatEnrolled(course.enrolled)} enrolled
            </span>
            {course.schedule && (
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <Clock className="h-4 w-4" />
                {course.schedule}
              </span>
            )}
          </div>

          <Separator />

          {/* Description — progressive disclosure */}
          <div>
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              About this course
            </h2>
            <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
              {displayDescription}
            </p>
            {course.description.length > DESCRIPTION_PREVIEW_LENGTH && (
              <Button
                variant="ghost"
                size="sm"
                className="mt-2 gap-1 text-primary"
                onClick={() => setDescriptionExpanded(!descriptionExpanded)}
              >
                {descriptionExpanded ? (
                  <>
                    Show less <ChevronUp className="h-4 w-4" />
                  </>
                ) : (
                  <>
                    Show more <ChevronDown className="h-4 w-4" />
                  </>
                )}
              </Button>
            )}
          </div>

          {/* Modules / Curriculum */}
          {course.modules && (
            <>
              <Separator />
              <div>
                <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <GraduationCap className="h-5 w-5" />
                  Curriculum
                </h2>
                <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                  {course.modules}
                </p>
              </div>
            </>
          )}
        </div>

        {/* Sidebar — right column */}
        <div className="flex flex-col gap-4">
          {/* CTA Card */}
          <Card>
            <CardContent className="pt-6 flex flex-col gap-4">
              <Button className="w-full gap-2" asChild>
                <a href={course.url} target="_blank" rel="noopener noreferrer">
                  View on Coursera
                  <ExternalLink className="h-4 w-4" />
                </a>
              </Button>
              <p className="text-xs text-center text-muted-foreground">
                Opens in a new tab on coursera.org
              </p>
            </CardContent>
          </Card>

          {/* Skills */}
          {course.skills.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <h3 className="font-semibold text-sm">Skills you&apos;ll gain</h3>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex flex-wrap gap-1.5">
                  {course.skills.map((skill) => (
                    <Badge key={skill} variant="secondary" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Course info summary */}
          <Card>
            <CardHeader className="pb-3">
              <h3 className="font-semibold text-sm">Course details</h3>
            </CardHeader>
            <CardContent className="pt-0">
              <dl className="flex flex-col gap-3 text-sm">
                {course.level && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Level</dt>
                    <dd className="font-medium">{course.level}</dd>
                  </div>
                )}
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Rating</dt>
                  <dd className="font-medium flex items-center gap-1">
                    <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                    {course.rating.toFixed(1)}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Enrolled</dt>
                  <dd className="font-medium">{course.enrolled.toLocaleString()}</dd>
                </div>
                {course.instructor && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Instructor</dt>
                    <dd className="font-medium text-right max-w-[60%] truncate">
                      {course.instructor}
                    </dd>
                  </div>
                )}
                {course.schedule && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Duration</dt>
                    <dd className="font-medium text-right max-w-[60%]">{course.schedule}</dd>
                  </div>
                )}
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Provider</dt>
                  <dd className="font-medium text-right max-w-[60%] truncate">
                    {course.organization}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          {/* Related courses placeholder */}
          <Card className="border-dashed">
            <CardContent className="pt-6 flex flex-col items-center gap-2 text-center text-muted-foreground">
              <BookOpen className="h-8 w-8 opacity-30" />
              <p className="text-sm font-medium">Related courses</p>
              <p className="text-xs">Coming soon — powered by AI similarity search</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

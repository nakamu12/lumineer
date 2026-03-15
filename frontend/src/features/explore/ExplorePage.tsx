import { useState } from "react"
import { Search, AlertCircle, BookOpen, Loader2 } from "lucide-react"
import { Input } from "@/lib/ui/input"
import { Button } from "@/lib/ui/button"
import { CourseCard } from "./components/CourseCard"
import { CourseCardSkeleton } from "./components/CourseCardSkeleton"
import { SearchFilters, type LevelFilter, type RatingFilter } from "./components/SearchFilters"
import { AiSummaryPanel } from "./components/AiSummaryPanel"
import { useCourseSearch } from "./hooks/useCourseSearch"

const SKELETON_COUNT = 6

export function ExplorePage() {
  const [query, setQuery] = useState("")
  const [level, setLevel] = useState<LevelFilter>("")
  const [minRating, setMinRating] = useState<RatingFilter>("")

  const { courses, total, aiSummary, isLoading, error, hasMore, loadMore } = useCourseSearch({
    query,
    level,
    minRating,
  })

  const handleClearFilters = () => {
    setLevel("")
    setMinRating("")
  }

  const hasQuery = query.trim().length > 0
  const hasResults = courses.length > 0
  const showEmpty = hasQuery && !isLoading && !error && !hasResults

  return (
    <div className="flex flex-col gap-6">
      {/* Page header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight">Explore Courses</h1>
        <p className="text-muted-foreground">Browse and search from 6,645+ courses</p>
      </div>

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search courses by topic, skill, or keyword..."
          className="pl-10 h-12 text-base"
          aria-label="Search courses"
        />
      </div>

      {/* Filters */}
      <SearchFilters
        level={level}
        minRating={minRating}
        onLevelChange={setLevel}
        onMinRatingChange={setMinRating}
        onClearFilters={handleClearFilters}
      />

      {/* AI Summary panel */}
      {aiSummary && <AiSummaryPanel text={aiSummary} />}

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-3 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-destructive">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <div>
            <p className="font-medium">Search failed</p>
            <p className="text-sm opacity-80">{error.message}</p>
          </div>
        </div>
      )}

      {/* Result count */}
      {hasResults && !isLoading && (
        <p className="text-sm text-muted-foreground">
          Showing <span className="font-medium text-foreground">{courses.length}</span> of{" "}
          <span className="font-medium text-foreground">{total.toLocaleString()}</span> results
          {query && (
            <>
              {" "}for{" "}
              <span className="font-medium text-foreground">&ldquo;{query}&rdquo;</span>
            </>
          )}
        </p>
      )}

      {/* Course grid — loading skeletons */}
      {isLoading && courses.length === 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
            <CourseCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Course grid — results */}
      {hasResults && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {courses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
            {/* Inline skeletons when loading more */}
            {isLoading &&
              Array.from({ length: 3 }).map((_, i) => <CourseCardSkeleton key={`more-${i}`} />)}
          </div>

          {/* Load more / pagination */}
          {hasMore && !isLoading && (
            <div className="flex justify-center pt-2">
              <Button
                variant="outline"
                onClick={loadMore}
                className="min-w-[160px]"
              >
                Load more courses
              </Button>
            </div>
          )}

          {isLoading && courses.length > 0 && (
            <div className="flex justify-center pt-2">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}
        </>
      )}

      {/* Empty state — no results */}
      {showEmpty && (
        <div className="flex flex-col items-center gap-3 py-16 text-center text-muted-foreground">
          <BookOpen className="h-12 w-12 opacity-30" />
          <p className="text-lg font-medium">No courses found</p>
          <p className="text-sm max-w-xs">
            Try a different keyword or adjust your filters.
          </p>
          <Button variant="outline" size="sm" onClick={handleClearFilters}>
            Clear filters
          </Button>
        </div>
      )}

      {/* Initial placeholder — before any search */}
      {!hasQuery && !isLoading && (
        <div className="flex flex-col items-center gap-3 py-16 text-center text-muted-foreground">
          <Search className="h-12 w-12 opacity-30" />
          <p className="text-lg font-medium">Search for courses</p>
          <p className="text-sm max-w-xs">
            Enter a keyword above to discover courses from Coursera&apos;s catalog.
          </p>
        </div>
      )}
    </div>
  )
}

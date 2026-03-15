import { X } from "lucide-react"
import { Button } from "@/lib/ui/button"
import { Select } from "@/lib/ui/select"

export type LevelFilter = "" | "Beginner" | "Intermediate" | "Advanced"
export type RatingFilter = "" | "4.0" | "4.5" | "4.7"

interface SearchFiltersProps {
  level: LevelFilter
  minRating: RatingFilter
  onLevelChange: (value: LevelFilter) => void
  onMinRatingChange: (value: RatingFilter) => void
  onClearFilters: () => void
}

export function SearchFilters({
  level,
  minRating,
  onLevelChange,
  onMinRatingChange,
  onClearFilters,
}: SearchFiltersProps) {
  const hasActiveFilters = level !== "" || minRating !== ""

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Select
        value={level}
        onChange={(e) => onLevelChange(e.target.value as LevelFilter)}
        className="w-auto min-w-[140px]"
        aria-label="Filter by level"
      >
        <option value="">All Levels</option>
        <option value="Beginner">Beginner</option>
        <option value="Intermediate">Intermediate</option>
        <option value="Advanced">Advanced</option>
      </Select>

      <Select
        value={minRating}
        onChange={(e) => onMinRatingChange(e.target.value as RatingFilter)}
        className="w-auto min-w-[140px]"
        aria-label="Filter by minimum rating"
      >
        <option value="">Any Rating</option>
        <option value="4.0">4.0+ Stars</option>
        <option value="4.5">4.5+ Stars</option>
        <option value="4.7">4.7+ Stars</option>
      </Select>

      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearFilters}
          className="gap-1.5 text-muted-foreground hover:text-foreground"
        >
          <X className="h-3.5 w-3.5" />
          Clear filters
        </Button>
      )}
    </div>
  )
}

export interface Course {
  id: string
  title: string
  description: string
  organization: string
  level: "Beginner" | "Intermediate" | "Advanced" | null
  rating: number
  enrolled: number
  skills: string[]
  url: string
  instructor: string | null
  schedule: string | null
  modules: string | null
}

export interface CourseSearchResult {
  courses: Course[]
  total: number
  summary?: string
  ai_summary?: string
}

export interface SkillGapAnalysis {
  current_skills: string[]
  target_skills: string[]
  gap_skills: string[]
  recommended_courses: Course[]
}

export interface LearningPath {
  id: string
  title: string
  description: string
  courses: Course[]
  estimated_duration: string
}

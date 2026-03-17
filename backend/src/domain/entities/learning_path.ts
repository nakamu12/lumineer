export type CourseRef = {
  course_id: string
  order: number
}

export type LearningPathEntity = {
  id: string
  title: string
  goal: string | null
  courses: CourseRef[]
  createdAt: Date
  updatedAt: Date
}

type CreateLearningPathParams = {
  id: string
  title: string
  goal: string | null
  courses: CourseRef[]
  createdAt: Date
  updatedAt: Date
}

export const LearningPathFactory = {
  create(params: CreateLearningPathParams): LearningPathEntity {
    const title = params.title.trim()
    if (title.length === 0) {
      throw new Error("Learning path title cannot be empty")
    }
    const courses = Array.isArray(params.courses) ? params.courses : []
    return {
      id: params.id,
      title,
      goal: params.goal,
      courses,
      createdAt: params.createdAt,
      updatedAt: params.updatedAt,
    }
  },
}

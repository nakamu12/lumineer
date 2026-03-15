/**
 * Course entity — core domain object.
 * Use CourseFactory.create() to instantiate; do NOT use `new Course()` directly.
 */

export type Course = {
  id: string;
  title: string;
  description: string;
  level: "Beginner" | "Intermediate" | "Advanced" | null;
  organization: string;
  rating: number;
  enrolled: number;
  skills: string[];
  url: string;
  instructor: string;
  schedule: string;
  modules: string;
};

type CourseInput = {
  id: string;
  title: string;
  description: string;
  level?: "Beginner" | "Intermediate" | "Advanced" | null;
  organization: string;
  rating: number;
  enrolled: number;
  skills?: string[];
  url: string;
  instructor?: string;
  schedule?: string;
  modules?: string;
};

/**
 * Factory for creating Course entities with validation.
 * Enforces the Factory pattern: all Course instances must come through here.
 */
export const CourseFactory = {
  create(input: CourseInput): Course {
    if (!input.id) {
      throw new Error("Course id is required");
    }
    if (!input.title) {
      throw new Error("Course title is required");
    }
    if (input.rating < 0 || input.rating > 5) {
      throw new Error(`Invalid rating: ${input.rating}. Must be between 0 and 5.`);
    }
    if (input.enrolled < 0) {
      throw new Error(`Invalid enrolled count: ${input.enrolled}. Must be non-negative.`);
    }

    return {
      id: input.id,
      title: input.title,
      description: input.description,
      level: input.level ?? null,
      organization: input.organization,
      rating: input.rating,
      enrolled: input.enrolled,
      skills: input.skills ?? [],
      url: input.url,
      instructor: input.instructor ?? "",
      schedule: input.schedule ?? "",
      modules: input.modules ?? "",
    };
  },
};

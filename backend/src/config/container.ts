import { AIProcessingClient } from "../infrastructure/llm/ai_processing_client.ts";
import { SearchCoursesUseCase } from "../domain/usecases/search_courses.ts";
import { ChatUseCase } from "../domain/usecases/chat.ts";

export type Container = {
  searchCoursesUseCase: SearchCoursesUseCase;
  chatUseCase: ChatUseCase;
};

export function createContainer(): Container {
  const aiProcessingClient = new AIProcessingClient();
  return {
    searchCoursesUseCase: new SearchCoursesUseCase(aiProcessingClient),
    chatUseCase: new ChatUseCase(aiProcessingClient),
  };
}

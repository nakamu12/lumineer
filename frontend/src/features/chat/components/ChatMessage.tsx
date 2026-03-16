import { Sparkles, User } from "lucide-react"
import { cn } from "@/lib/utils"
import { CourseCardMini } from "./CourseCardMini"
import type { Course } from "@/lib/types/course"

export interface ChatMessageData {
  id: string
  role: "user" | "assistant"
  content: string
  courses?: Course[]
  timestamp: Date
}

interface ChatMessageProps {
  message: ChatMessageData
}

function renderContent(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="rounded bg-muted px-1 py-0.5 text-xs font-mono">
          {part.slice(1, -1)}
        </code>
      )
    }
    return <span key={i}>{part}</span>
  })
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user"

  return (
    <div className={cn("flex items-start gap-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-primary text-primary-foreground" : "bg-primary/10",
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4 text-primary" />}
      </div>

      {/* Bubble */}
      <div className={cn("flex flex-col gap-2 max-w-[80%]", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "rounded-tr-sm bg-primary text-primary-foreground"
              : "rounded-tl-sm bg-muted text-foreground",
          )}
        >
          {renderContent(message.content)}
        </div>

        {/* Inline course cards */}
        {message.courses && message.courses.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full">
            {message.courses.map((course) => (
              <CourseCardMini key={course.id} course={course} />
            ))}
          </div>
        )}

        <span className="text-[10px] text-muted-foreground px-1">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  )
}

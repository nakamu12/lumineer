import { MessageSquare, Plus } from "lucide-react"
import { Button } from "@/lib/ui/button"
import { cn } from "@/lib/utils"
import type { ChatSession } from "../hooks/useChatSessions"

interface ChatSessionListProps {
  sessions: ChatSession[]
  currentSessionId: string | null
  onSelectSession: (sessionId: string) => void
  onNewChat: () => void
}

export function ChatSessionList({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
}: ChatSessionListProps) {
  return (
    <div className="flex flex-col gap-2">
      <Button variant="outline" size="sm" className="w-full gap-2" onClick={onNewChat}>
        <Plus className="h-4 w-4" />
        New Chat
      </Button>

      {sessions.length === 0 && (
        <p className="text-xs text-muted-foreground text-center py-4">No conversations yet</p>
      )}

      <div className="flex flex-col gap-1">
        {sessions.map((session) => (
          <button
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-muted",
              currentSessionId === session.id && "bg-muted font-medium",
            )}
          >
            <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="truncate">{session.title}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

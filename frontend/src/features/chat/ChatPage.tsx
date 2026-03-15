import { useState } from "react"
import { Send } from "lucide-react"
import { Input } from "@/lib/ui/input"
import { Button } from "@/lib/ui/button"

export function ChatPage() {
  const [message, setMessage] = useState("")

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex flex-col gap-2 mb-6">
        <h1 className="text-3xl font-bold">AI Course Assistant</h1>
        <p className="text-muted-foreground">
          Ask me anything about courses, skill gaps, or learning paths
        </p>
      </div>
      <div className="flex-1 rounded-lg border bg-muted/20 p-4 overflow-y-auto mb-4">
        <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
          <p>Start a conversation to discover the perfect course for you</p>
        </div>
      </div>
      <div className="flex gap-2">
        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask about courses, skills, or learning paths..."
          onKeyDown={(e) => e.key === "Enter" && setMessage("")}
        />
        <Button size="icon" onClick={() => setMessage("")}>
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

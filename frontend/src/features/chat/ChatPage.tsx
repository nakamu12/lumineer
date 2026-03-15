import { useState, useRef, useEffect } from "react"
import { Trash2 } from "lucide-react"
import { Button } from "@/lib/ui/button"
import { ChatMessage } from "./components/ChatMessage"
import { ChatInput } from "./components/ChatInput"
import { TypingIndicator } from "./components/TypingIndicator"
import { SuggestedPrompts } from "./components/SuggestedPrompts"
import { useChat } from "./hooks/useChat"

export function ChatPage() {
  const [input, setInput] = useState("")
  const { messages, isLoading, isStreaming, sendMessage, clearChat } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const handleSubmit = async () => {
    const text = input.trim()
    if (!text) return
    setInput("")
    await sendMessage(text)
  }

  const handleSuggest = (text: string) => {
    setInput(text)
    sendMessage(text)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div>
          <h1 className="text-2xl font-bold">Chat with Lumineer AI</h1>
          <p className="text-sm text-muted-foreground">
            Discover courses, analyze skill gaps, and generate learning paths
          </p>
        </div>
        {messages.length > 0 && (
          <Button variant="ghost" size="sm" onClick={clearChat} className="gap-2 text-muted-foreground">
            <Trash2 className="h-4 w-4" />
            Clear
          </Button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto rounded-xl border bg-muted/10 p-4">
        {messages.length === 0 ? (
          <SuggestedPrompts onSelect={handleSuggest} />
        ) : (
          <div className="flex flex-col gap-6">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="mt-3 shrink-0">
        <ChatInput
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          disabled={isLoading || isStreaming}
          isStreaming={isStreaming}
        />
        <p className="text-center text-[11px] text-muted-foreground mt-2">
          Lumineer AI can make mistakes. Verify important information.
        </p>
      </div>
    </div>
  )
}

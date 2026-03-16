import { useRef, useEffect, KeyboardEvent } from "react"
import { ArrowUp } from "lucide-react"
import { Button } from "@/lib/ui/button"
import { cn } from "@/lib/utils"

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  disabled?: boolean
  isStreaming?: boolean
}

export function ChatInput({ value, onChange, onSubmit, disabled, isStreaming }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = "auto"
    ta.style.height = `${Math.min(ta.scrollHeight, 128)}px`
  }, [value])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (!disabled && value.trim()) onSubmit()
    }
  }

  return (
    <div className="relative flex items-end gap-2 rounded-2xl border bg-background p-2 shadow-sm focus-within:ring-1 focus-within:ring-ring">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={
          isStreaming ? "AI is thinking..." : "Ask about courses, skills, or learning paths..."
        }
        disabled={disabled}
        rows={1}
        className={cn(
          "flex-1 resize-none bg-transparent px-2 py-1 text-sm outline-none placeholder:text-muted-foreground",
          "min-h-[36px] max-h-32 scrollbar-thin disabled:cursor-not-allowed disabled:opacity-50",
        )}
      />
      <Button
        size="icon"
        className="h-8 w-8 shrink-0 rounded-xl"
        onClick={onSubmit}
        disabled={disabled || !value.trim()}
      >
        <ArrowUp className="h-4 w-4" />
      </Button>
    </div>
  )
}

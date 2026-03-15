import { useState } from "react"
import { Sparkles, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/lib/ui/button"
import { cn } from "@/lib/utils"

interface AiSummaryPanelProps {
  text: string
  isStreaming?: boolean
}

export function AiSummaryPanel({ text, isStreaming = false }: AiSummaryPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  if (!text && !isStreaming) return null

  return (
    <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-primary">
          <Sparkles className="h-4 w-4" />
          <span className="text-sm font-medium">AI Summary</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-muted-foreground hover:text-foreground md:hidden"
          onClick={() => setIsCollapsed((prev) => !prev)}
          aria-label={isCollapsed ? "Expand summary" : "Collapse summary"}
        >
          {isCollapsed ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronUp className="h-3.5 w-3.5" />
          )}
        </Button>
      </div>

      <div
        className={cn(
          "text-sm text-foreground leading-relaxed overflow-hidden transition-all duration-200",
          isCollapsed ? "max-h-0 md:max-h-none" : "max-h-none"
        )}
      >
        {isStreaming && !text ? (
          <span className="text-muted-foreground animate-pulse">Generating summary...</span>
        ) : (
          <>
            {text}
            {isStreaming && (
              <span className="inline-block w-0.5 h-4 bg-primary ml-0.5 animate-[blink_1s_ease-in-out_infinite]" />
            )}
          </>
        )}
      </div>
    </div>
  )
}

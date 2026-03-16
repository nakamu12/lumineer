import { Search, Target, Map, BookOpen } from "lucide-react"
import { Button } from "@/lib/ui/button"

const prompts = [
  { icon: Search, text: "Find Python courses for beginners" },
  { icon: Target, text: "Analyze my skill gap for data science" },
  { icon: Map, text: "Create a 3-month web dev learning path" },
  { icon: BookOpen, text: "Top machine learning courses" },
]

interface SuggestedPromptsProps {
  onSelect: (text: string) => void
}

export function SuggestedPrompts({ onSelect }: SuggestedPromptsProps) {
  return (
    <div className="flex flex-col items-center gap-6 py-12">
      <div className="text-center">
        <h2 className="text-xl font-semibold">How can I help you today?</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Ask me about courses, skill gaps, or learning paths
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
        {prompts.map(({ icon: Icon, text }) => (
          <Button
            key={text}
            variant="outline"
            className="h-auto py-3 px-4 justify-start gap-3 text-left hover:border-primary/50 hover:bg-primary/5"
            onClick={() => onSelect(text)}
          >
            <Icon className="h-4 w-4 shrink-0 text-primary" />
            <span className="text-sm">{text}</span>
          </Button>
        ))}
      </div>
    </div>
  )
}

import { Map } from "lucide-react"

export function MyPathPage() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">My Learning Path</h1>
        <p className="text-muted-foreground">Track your progress and manage your learning journey</p>
      </div>
      <div className="flex flex-col items-center justify-center py-16 gap-4 text-muted-foreground">
        <Map className="h-12 w-12" />
        <p className="text-lg">No learning path yet</p>
        <p className="text-sm">Chat with the AI assistant to generate a personalized learning path</p>
      </div>
    </div>
  )
}

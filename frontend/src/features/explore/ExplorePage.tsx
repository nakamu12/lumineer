import { Search } from "lucide-react"
import { Input } from "@/lib/ui/input"
import { Button } from "@/lib/ui/button"

export function ExplorePage() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Explore Courses</h1>
        <p className="text-muted-foreground">Browse and search from 6,645+ courses</p>
      </div>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search courses..." className="pl-9" />
        </div>
        <Button>Search</Button>
      </div>
      <div className="text-center text-muted-foreground py-12">
        Search for courses to get started
      </div>
    </div>
  )
}

import { Link } from "react-router-dom"
import { Search, BookOpen, Target, Map } from "lucide-react"
import { Button } from "@/lib/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/lib/ui/card"

const features = [
  {
    icon: Search,
    title: "Smart Course Search",
    description: "Find the perfect course using natural language. Our AI understands what you want to learn.",
  },
  {
    icon: Target,
    title: "Skill Gap Analysis",
    description: "Discover what skills you need to reach your goals and get personalized course recommendations.",
  },
  {
    icon: Map,
    title: "Learning Path Generation",
    description: "Get a structured learning roadmap tailored to your timeline and objectives.",
  },
]

export function HomePage() {
  return (
    <div className="flex flex-col gap-16">
      {/* Hero */}
      <section className="flex flex-col items-center gap-6 pt-12 text-center">
        <div className="flex items-center gap-2">
          <BookOpen className="h-8 w-8 text-primary" />
          <span className="text-lg font-semibold text-muted-foreground">Lumineer</span>
        </div>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Illuminate Your
          <br />
          <span className="text-primary">Learning Journey</span>
        </h1>
        <p className="max-w-xl text-lg text-muted-foreground">
          Discover the perfect courses from 6,645+ Coursera offerings. AI-powered search, skill gap analysis,
          and personalized learning paths — all in one place.
        </p>
        <div className="flex gap-4">
          <Button asChild size="lg">
            <Link to="/chat">Start Learning</Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link to="/explore">Explore Courses</Link>
          </Button>
        </div>
      </section>

      {/* Features */}
      <section className="grid gap-6 sm:grid-cols-3">
        {features.map((feature) => (
          <Card key={feature.title}>
            <CardHeader>
              <feature.icon className="h-8 w-8 text-primary" />
              <CardTitle className="text-lg">{feature.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>{feature.description}</CardDescription>
            </CardContent>
          </Card>
        ))}
      </section>
    </div>
  )
}

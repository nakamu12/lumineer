import { Link } from "react-router-dom"
import { Search, BookOpen, Target, Map, Zap, Users, GraduationCap } from "lucide-react"
import { Button } from "@/lib/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/lib/ui/card"

const features = [
  {
    icon: Search,
    title: "Smart Course Search",
    description:
      "Find the perfect course using natural language. Our AI understands what you want to learn.",
    iconColor: "text-teal-500",
    glowColor: "group-hover:shadow-teal-500/20",
    borderColor: "hover:border-teal-500/30",
    bgGradient: "from-teal-500/5 to-transparent",
  },
  {
    icon: Target,
    title: "Skill Gap Analysis",
    description:
      "Discover what skills you need to reach your goals and get personalized course recommendations.",
    iconColor: "text-blue-500",
    glowColor: "group-hover:shadow-blue-500/20",
    borderColor: "hover:border-blue-500/30",
    bgGradient: "from-blue-500/5 to-transparent",
  },
  {
    icon: Map,
    title: "Learning Path Generation",
    description: "Get a structured learning roadmap tailored to your timeline and objectives.",
    iconColor: "text-teal-400",
    glowColor: "group-hover:shadow-teal-400/20",
    borderColor: "hover:border-teal-400/30",
    bgGradient: "from-teal-400/5 to-transparent",
  },
]

const stats = [
  {
    icon: GraduationCap,
    value: "6,645+",
    label: "Courses",
    iconColor: "text-teal-500",
  },
  {
    icon: Zap,
    value: "AI-Powered",
    label: "Search & Analysis",
    iconColor: "text-blue-500",
  },
  {
    icon: Users,
    value: "3 Agents",
    label: "Working for You",
    iconColor: "text-teal-400",
  },
]

export function HomePage() {
  return (
    <div className="flex flex-col gap-20">
      {/* Hero */}
      <section className="relative flex flex-col items-center gap-8 pt-16 text-center">
        {/* Background blob */}
        <div
          className="pointer-events-none absolute inset-0 -z-10 overflow-hidden"
          aria-hidden="true"
        >
          <div className="absolute left-1/2 top-0 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/4 rounded-full bg-gradient-radial from-teal-500/10 via-blue-500/5 to-transparent blur-3xl" />
        </div>

        {/* Badge */}
        <div className="flex items-center gap-2 rounded-full border border-teal-500/20 bg-teal-500/5 px-4 py-1.5">
          <BookOpen className="h-4 w-4 text-teal-500" />
          <span className="text-sm font-medium text-teal-600 dark:text-teal-400">
            Intelligent Course Discovery
          </span>
        </div>

        {/* Heading */}
        <h1 className="max-w-3xl text-5xl font-bold tracking-tight sm:text-6xl">
          Illuminate Your
          <br />
          <span className="bg-gradient-to-r from-teal-500 to-blue-500 bg-clip-text text-transparent">
            Learning Journey
          </span>
        </h1>

        <p className="max-w-xl text-lg text-muted-foreground">
          Discover the perfect courses from 6,645+ Coursera offerings. AI-powered search, skill gap
          analysis, and personalized learning paths — all in one place.
        </p>

        {/* CTA buttons */}
        <div className="flex flex-wrap justify-center gap-4">
          <Button
            asChild
            size="lg"
            className="relative overflow-hidden bg-gradient-to-r from-teal-500 to-teal-600 text-white shadow-lg shadow-teal-500/25 transition-all hover:scale-105 hover:shadow-teal-500/40"
          >
            <Link to="/chat">
              <Zap className="mr-2 h-4 w-4" />
              Start Learning
            </Link>
          </Button>
          <Button
            asChild
            variant="outline"
            size="lg"
            className="border-teal-500/30 transition-all hover:scale-105 hover:border-teal-500/60 hover:bg-teal-500/5"
          >
            <Link to="/explore">Explore Courses</Link>
          </Button>
        </div>
      </section>

      {/* Stats */}
      <section className="grid gap-6 sm:grid-cols-3">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="flex flex-col items-center gap-2 rounded-xl border border-border/50 bg-card/50 py-6 text-center backdrop-blur-sm"
          >
            <stat.icon className={`h-6 w-6 ${stat.iconColor}`} />
            <span className="text-2xl font-bold">{stat.value}</span>
            <span className="text-sm text-muted-foreground">{stat.label}</span>
          </div>
        ))}
      </section>

      {/* Features */}
      <section className="flex flex-col gap-8">
        <div className="text-center">
          <h2 className="text-2xl font-semibold tracking-tight">
            Everything you need to learn smarter
          </h2>
          <p className="mt-2 text-muted-foreground">
            Three AI agents working together to accelerate your growth
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-3">
          {features.map((feature) => (
            <Card
              key={feature.title}
              className={`group relative overflow-hidden border transition-all duration-300 ${feature.borderColor} hover:-translate-y-1 hover:shadow-lg ${feature.glowColor}`}
            >
              {/* Subtle gradient background */}
              <div
                className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${feature.bgGradient} opacity-0 transition-opacity duration-300 group-hover:opacity-100`}
                aria-hidden="true"
              />
              <CardHeader className="relative">
                <div
                  className={`mb-1 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-muted/60 transition-all duration-300 group-hover:scale-110 ${feature.iconColor}`}
                >
                  <feature.icon className="h-5 w-5" />
                </div>
                <CardTitle className="text-lg">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent className="relative">
                <CardDescription>{feature.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  )
}

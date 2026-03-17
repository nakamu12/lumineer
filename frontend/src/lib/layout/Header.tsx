import { Link, useLocation } from "react-router-dom"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/", label: "Home" },
  { href: "/explore", label: "Explore" },
  { href: "/chat", label: "Chat" },
  { href: "/path", label: "My Path" },
  { href: "/settings", label: "Settings" },
]

export function Header() {
  const location = useLocation()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <Link to="/" className="flex items-center gap-1.5">
          <img src="/logo.png" alt="Lumineer" className="h-6 w-6" />
          <span
            className="bg-gradient-to-r from-teal-500 to-blue-500 bg-clip-text text-transparent font-semibold"
            style={{ fontFamily: "'Outfit', sans-serif" }}
          >
            Lumineer
          </span>
        </Link>
        <nav className="ml-auto flex items-center gap-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                "px-3 py-2 text-sm rounded-md transition-colors hover:text-primary",
                location.pathname === item.href
                  ? "text-primary font-medium"
                  : "text-muted-foreground",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}

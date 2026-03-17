import { Link, useLocation, useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth/AuthContext"
import { Button } from "@/lib/ui/button"
import { LogOut } from "lucide-react"

const navItems = [
  { href: "/", label: "Home" },
  { href: "/explore", label: "Explore" },
  { href: "/chat", label: "Chat" },
  { href: "/path", label: "My Path" },
  { href: "/settings", label: "Settings" },
]

export function Header() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate("/")
  }

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

          <div className="ml-2 flex items-center gap-2 border-l pl-3">
            {isAuthenticated ? (
              <>
                <span className="text-sm text-muted-foreground">{user?.display_name}</span>
                <Button variant="ghost" size="sm" onClick={handleLogout} title="Sign out">
                  <LogOut className="h-4 w-4" />
                </Button>
              </>
            ) : (
              <Button variant="default" size="sm" asChild>
                <Link to="/login">Sign In</Link>
              </Button>
            )}
          </div>
        </nav>
      </div>
    </header>
  )
}

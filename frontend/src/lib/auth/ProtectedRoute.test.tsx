import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter, Routes, Route } from "react-router-dom"
import { ProtectedRoute } from "./ProtectedRoute"

// Mock useAuth to control auth state
vi.mock("./AuthContext", () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from "./AuthContext"

const mockedUseAuth = vi.mocked(useAuth)

function renderProtectedRoute(initialPath = "/protected") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route
          path="/protected"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("ProtectedRoute", () => {
  it("renders children when authenticated", () => {
    mockedUseAuth.mockReturnValue({
      user: { id: "1", email: "a@b.com", display_name: "A" },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    renderProtectedRoute()
    expect(screen.getByText("Protected Content")).toBeInTheDocument()
  })

  it("redirects to /login when not authenticated", () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    renderProtectedRoute()
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument()
    expect(screen.getByText("Login Page")).toBeInTheDocument()
  })

  it("shows loading spinner when auth is loading", () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    const { container } = renderProtectedRoute()
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument()
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument()
    // Spinner element exists
    expect(container.querySelector(".animate-spin")).toBeInTheDocument()
  })
})

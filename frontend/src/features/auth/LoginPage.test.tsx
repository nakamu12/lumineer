import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { LoginPage } from "./LoginPage"

const mockLogin = vi.fn()
const mockRegister = vi.fn()

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: mockLogin,
    register: mockRegister,
    logout: vi.fn(),
  }),
}))

function renderLoginPage() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <LoginPage />
    </MemoryRouter>,
  )
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("renders login form by default", () => {
    renderLoginPage()

    expect(screen.getByLabelText("Email")).toBeInTheDocument()
    expect(screen.getByLabelText("Password")).toBeInTheDocument()
    expect(screen.queryByLabelText("Display Name")).not.toBeInTheDocument()

    const submitBtn = screen.getAllByRole("button").find((b) => b.getAttribute("type") === "submit")
    expect(submitBtn).toHaveTextContent("Sign In")
  })

  it("switches to register form when Create Account tab is clicked", () => {
    renderLoginPage()

    // Click the tab button (type="button"), not the submit
    const tabButton = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "button" && b.textContent === "Create Account")
    fireEvent.click(tabButton!)

    expect(screen.getByLabelText("Display Name")).toBeInTheDocument()
    expect(screen.getByLabelText("Email")).toBeInTheDocument()
    expect(screen.getByLabelText("Password")).toBeInTheDocument()
  })

  it("calls login on form submit in login mode", async () => {
    mockLogin.mockResolvedValueOnce(undefined)
    renderLoginPage()

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "test@example.com" } })
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "Password1" } })

    const submitBtn = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "submit")!
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith("test@example.com", "Password1")
    })
  })

  it("calls register on form submit in register mode", async () => {
    mockRegister.mockResolvedValueOnce(undefined)
    renderLoginPage()

    // Switch to register mode
    const tabButton = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "button" && b.textContent === "Create Account")
    fireEvent.click(tabButton!)

    fireEvent.change(screen.getByLabelText("Display Name"), { target: { value: "Test User" } })
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "new@example.com" } })
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "Password1" } })

    const submitBtn = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "submit")!
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith("new@example.com", "Password1", "Test User")
    })
  })

  it("displays error message on login failure", async () => {
    mockLogin.mockRejectedValueOnce(new Error("Invalid credentials"))
    renderLoginPage()

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "bad@example.com" } })
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong" } })

    const submitBtn = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "submit")!
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument()
    })
  })

  it("clears error when switching modes", async () => {
    mockLogin.mockRejectedValueOnce(new Error("Invalid credentials"))
    renderLoginPage()

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "bad@example.com" } })
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong" } })

    const submitBtn = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "submit")!
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument()
    })

    // Switch to register mode
    const tabButton = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "button" && b.textContent === "Create Account")
    fireEvent.click(tabButton!)

    expect(screen.queryByText("Invalid credentials")).not.toBeInTheDocument()
  })

  it("shows password requirements hint in register mode", () => {
    renderLoginPage()

    expect(screen.queryByText(/Must include uppercase/)).not.toBeInTheDocument()

    const tabButton = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "button" && b.textContent === "Create Account")
    fireEvent.click(tabButton!)

    expect(screen.getByText(/Must include uppercase/)).toBeInTheDocument()
  })
})

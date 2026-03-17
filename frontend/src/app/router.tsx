import { createBrowserRouter } from "react-router-dom"
import { PageLayout } from "@/lib/layout/PageLayout"
import { ProtectedRoute } from "@/lib/auth/ProtectedRoute"
import { HomePage } from "@/features/home/HomePage"
import { ExplorePage } from "@/features/explore/ExplorePage"
import { ChatPage } from "@/features/chat/ChatPage"
import { MyPathPage } from "@/features/path/MyPathPage"
import { SettingsPage } from "@/features/settings/SettingsPage"
import { CourseDetailPage } from "@/features/course/CourseDetailPage"
import { LoginPage } from "@/features/auth/LoginPage"

export const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <PageLayout>
        <HomePage />
      </PageLayout>
    ),
  },
  {
    path: "/explore",
    element: (
      <PageLayout>
        <ExplorePage />
      </PageLayout>
    ),
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/chat",
    element: (
      <PageLayout>
        <ProtectedRoute>
          <ChatPage />
        </ProtectedRoute>
      </PageLayout>
    ),
  },
  {
    path: "/path",
    element: (
      <PageLayout>
        <ProtectedRoute>
          <MyPathPage />
        </ProtectedRoute>
      </PageLayout>
    ),
  },
  {
    path: "/course/:id",
    element: (
      <PageLayout>
        <CourseDetailPage />
      </PageLayout>
    ),
  },
  {
    path: "/settings",
    element: (
      <PageLayout>
        <ProtectedRoute>
          <SettingsPage />
        </ProtectedRoute>
      </PageLayout>
    ),
  },
])

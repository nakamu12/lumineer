import { createBrowserRouter } from "react-router-dom"
import { PageLayout } from "@/lib/layout/PageLayout"
import { HomePage } from "@/features/home/HomePage"
import { ExplorePage } from "@/features/explore/ExplorePage"
import { ChatPage } from "@/features/chat/ChatPage"
import { MyPathPage } from "@/features/path/MyPathPage"
import { SettingsPage } from "@/features/settings/SettingsPage"

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
    path: "/chat",
    element: (
      <PageLayout>
        <ChatPage />
      </PageLayout>
    ),
  },
  {
    path: "/path",
    element: (
      <PageLayout>
        <MyPathPage />
      </PageLayout>
    ),
  },
  {
    path: "/settings",
    element: (
      <PageLayout>
        <SettingsPage />
      </PageLayout>
    ),
  },
])

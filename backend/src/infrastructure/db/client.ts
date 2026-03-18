import { drizzle } from "drizzle-orm/postgres-js"
import postgres from "postgres"
import { getSettings } from "../../config/settings.ts"
import * as schema from "./schema.ts"

let dbInstance: ReturnType<typeof drizzle<typeof schema>> | null = null

export function getDb(): ReturnType<typeof drizzle<typeof schema>> {
  if (dbInstance) {
    return dbInstance
  }

  const { DATABASE_URL } = getSettings()

  // Parse DATABASE_URL to support Unix socket via ?host=/ parameter (Cloud SQL Auth Proxy)
  const url = new URL(DATABASE_URL)
  const socketHost = url.searchParams.get("host")

  let client: ReturnType<typeof postgres>
  if (socketHost?.startsWith("/")) {
    client = postgres({
      host: socketHost,
      user: url.username ? decodeURIComponent(url.username) : undefined,
      password: url.password ? decodeURIComponent(url.password) : undefined,
      database: url.pathname.slice(1),
    })
  } else {
    client = postgres(DATABASE_URL)
  }

  dbInstance = drizzle(client, { schema })
  return dbInstance
}

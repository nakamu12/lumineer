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
  const client = postgres(DATABASE_URL)
  dbInstance = drizzle(client, { schema })
  return dbInstance
}

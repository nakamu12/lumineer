/**
 * Seed script for demo data.
 * Idempotent — safe to run multiple times.
 * Usage: bun run db:seed
 */

import { getDb } from "../infrastructure/db/client.ts"
import { users } from "../infrastructure/db/schema.ts"
import { BcryptPasswordHasher } from "../infrastructure/auth/password.ts"

const passwordHasher = new BcryptPasswordHasher()

const DEMO_USERS = [
  {
    email: "demo@lumineer.app",
    password: "demo1234",
    displayName: "Demo User",
  },
]

async function seed(): Promise<void> {
  const db = getDb()
  console.log("Seeding demo users...")

  for (const u of DEMO_USERS) {
    const passwordHash = await passwordHasher.hash(u.password)
    await db
      .insert(users)
      .values({
        email: u.email,
        passwordHash,
        displayName: u.displayName,
      })
      .onConflictDoNothing()
    console.log(`  ✓ ${u.email}`)
  }

  console.log("Seeding complete.")
  process.exit(0)
}

seed().catch((err) => {
  console.error("Seed failed:", err)
  process.exit(1)
})

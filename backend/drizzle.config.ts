import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/infrastructure/db/schema.ts",
  out: "./drizzle/migrations",
  dialect: "postgresql",
  dbCredentials: {
    url:
      process.env["DATABASE_URL"] ??
      "postgres://lumineer:lumineer@localhost:5432/lumineer",
  },
});

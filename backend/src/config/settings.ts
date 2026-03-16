/**
 * Application settings loaded from environment variables.
 * Dev: defaults work out of the box (only OPENAI_API_KEY required in AI layer).
 * Prod: CI/CD injects all values via GitHub Secrets → Cloud Run env vars.
 */

export type Settings = {
  APP_ENV: "dev" | "prod";
  PORT: number;
  AI_PROCESSING_URL: string;
  DATABASE_URL: string;
  JWT_SECRET: string;
  JWT_ACCESS_EXPIRES: string;
  JWT_REFRESH_EXPIRES: string;
};

let cachedSettings: Settings | null = null;

export function getSettings(): Settings {
  if (cachedSettings) {
    return cachedSettings;
  }

  const appEnv = process.env["APP_ENV"] ?? "dev";
  if (appEnv !== "dev" && appEnv !== "prod") {
    throw new Error(`Invalid APP_ENV: "${appEnv}". Must be "dev" or "prod".`);
  }

  const portRaw = process.env["PORT"] ?? "3001";
  const port = parseInt(portRaw, 10);
  if (isNaN(port)) {
    throw new Error(`Invalid PORT: "${portRaw}". Must be a number.`);
  }

  const databaseUrl =
    process.env["DATABASE_URL"] ??
    "postgres://lumineer:lumineer@localhost:5432/lumineer";

  const jwtSecret = process.env["JWT_SECRET"] ?? "dev-secret-change-in-prod-min-16chars";

  cachedSettings = {
    APP_ENV: appEnv,
    PORT: port,
    AI_PROCESSING_URL:
      process.env["AI_PROCESSING_URL"] ?? "http://ai-processing:8000",
    DATABASE_URL: databaseUrl,
    JWT_SECRET: jwtSecret,
    JWT_ACCESS_EXPIRES: process.env["JWT_ACCESS_EXPIRES"] ?? "15m",
    JWT_REFRESH_EXPIRES: process.env["JWT_REFRESH_EXPIRES"] ?? "7d",
  };

  return cachedSettings;
}

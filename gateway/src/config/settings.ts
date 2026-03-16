export type Settings = {
  PORT: number;
  BACKEND_URL: string;
  ALLOWED_ORIGINS: string[];
  RATE_LIMIT_MAX: number;
  RATE_LIMIT_WINDOW_MS: number;
};

let cached: Settings | null = null;

export function getSettings(): Settings {
  if (cached) return cached;

  cached = {
    PORT: parseInt(process.env["PORT"] ?? "3000", 10),
    BACKEND_URL: process.env["BACKEND_URL"] ?? "http://backend:3001",
    ALLOWED_ORIGINS: (process.env["ALLOWED_ORIGINS"] ?? "http://localhost:5173").split(","),
    RATE_LIMIT_MAX: parseInt(process.env["RATE_LIMIT_MAX"] ?? "100", 10),
    RATE_LIMIT_WINDOW_MS: parseInt(process.env["RATE_LIMIT_WINDOW_MS"] ?? "60000", 10),
  };

  return cached;
}

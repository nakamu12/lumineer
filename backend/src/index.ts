import { createContainer } from "./config/container.ts";
import { createRouter } from "./interfaces/api/routes.ts";
import { getSettings } from "./config/settings.ts";

const settings = getSettings();
const container = createContainer();
const app = createRouter(container);

export default {
  port: settings.PORT,
  fetch: app.fetch,
};

console.log(`Lumineer API running on port ${settings.PORT}`);

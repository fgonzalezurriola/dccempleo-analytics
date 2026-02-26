// @ts-check
import { defineConfig } from 'astro/config';

import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';

const site =
  process.env.SITE_URL
  ?? process.env.PUBLIC_SITE_URL
  ?? (process.env.VERCEL_PROJECT_PRODUCTION_URL
    ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
    : 'https://dccempleo-analytics.vercel.app');

// https://astro.build/config
export default defineConfig({
  site,
  integrations: [react(), sitemap()],
});

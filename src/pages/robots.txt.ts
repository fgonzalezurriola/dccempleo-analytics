import type { APIRoute } from 'astro';

export const prerender = true;

export const GET: APIRoute = ({ site }) => {
  const baseUrl = (site ?? new URL('https://dccempleo-analytics.vercel.app')).toString().replace(/\/$/, '');
  const body = `User-agent: *\nAllow: /\n\nSitemap: ${baseUrl}/sitemap-index.xml\n`;

  return new Response(body, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
    },
  });
};

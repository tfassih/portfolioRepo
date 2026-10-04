import { defineMiddleware } from "astro:middleware";
import { get } from "./lib/backend.js";
export const onRequest = defineMiddleware(async (context, next) => {
  const path = context.url.pathname;
  try {
    if (!path.startsWith("/api/") && !path.endsWith(".xml") && !path.endsWith(".txt")) {
      context.locals.site = await get("/api/site/");
    }
    const response = await next();
    const privatePage = path.startsWith("/api/") || path.startsWith("/subscribe/");
    response.headers.set(
      "Cache-Control",
      privatePage ? "no-store" : "public, max-age=0, s-maxage=30",
    );
    response.headers.set("X-Content-Type-Options", "nosniff");
    response.headers.set(
      "Referrer-Policy",
      privatePage ? "no-referrer" : "strict-origin-when-cross-origin",
    );
    response.headers.set("X-Frame-Options", "DENY");
    if (import.meta.env.PROD) {
      const api = new URL(import.meta.env.PUBLIC_API_ORIGIN).origin;
      response.headers.set(
        "Content-Security-Policy",
        `default-src 'self'; img-src 'self' ${api} data:; media-src 'self' ${api}; ` +
          `connect-src 'self'; script-src 'self' 'unsafe-inline'; ` +
          `style-src 'self' 'unsafe-inline'; object-src 'none'; ` +
          `base-uri 'self'; form-action 'self'; frame-ancestors 'none'`,
      );
    }
    return response;
  } catch (error) {
    console.error("Content request failed:", error.status || "unavailable");
    return new Response(
      '<!doctype html><html lang="en"><meta name="viewport" ' +
        'content="width=device-width"><title>Temporarily unavailable</title>' +
        '<body style="font:18px/1.6 system-ui;max-width:40rem;margin:10vh auto;padding:24px">' +
        "<h1>Please try again shortly.</h1><p>The content service is temporarily unavailable.</p>" +
        '<a href="/">Try the homepage</a></body></html>',
      {
        status: 503,
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "no-store",
          "Retry-After": "60",
        },
      },
    );
  }
});
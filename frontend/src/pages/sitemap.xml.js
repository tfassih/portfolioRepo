import { get } from "../lib/backend.js";

const xml = (value) =>
  value.replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" })[c],
  );
export async function GET({ site }) {
  const data = await get("/api/sitemap/");
  const fixed = [
    "/",
    "/resume/",
    "/art/",
    "/art/images/",
    "/art/videos/",
    "/writing/",
    "/software/",
    "/blog/",
    "/contact/",
    "/privacy/",
  ];
  const urls = fixed.map((path) => ({ path })).concat(data.items);
  return new Response(
    '<?xml version="1.0" encoding="UTF-8"?>' +
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
      urls
        .map(
          (item) =>
            `<url><loc>${xml(new URL(item.path, site).href)}</loc>` +
            (item.updated ? `<lastmod>${item.updated}</lastmod>` : "") +
            "</url>",
        )
        .join("") +
      "</urlset>",
    { headers: { "Content-Type": "application/xml; charset=utf-8" } },
  );
}
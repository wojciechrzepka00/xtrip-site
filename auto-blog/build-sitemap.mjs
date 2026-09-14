// Generuje kompletny sitemap.xml ze wszystkich publicznych stron .html
// (strona główna + wersje językowe + blog + artykuły). Uruchamiane po generacji.
import fs from "fs";
import path from "path";

const DOMAIN = "https://krakow-transfers.com";
const ROOT = process.cwd();
const SKIP = new Set(["payments-backend", "auto-blog", "google-calendar-system", ".github", "node_modules", ".git"]);
const SKIP_FILES = new Set(["index-preview.html"]);

const urls = [];
function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.isDirectory()) {
      if (SKIP.has(e.name)) continue;
      walk(path.join(dir, e.name));
    } else if (e.isFile() && e.name.endsWith(".html") && !SKIP_FILES.has(e.name)) {
      let rel = path.relative(ROOT, path.join(dir, e.name)).split(path.sep).join("/");
      // index.html -> katalog; reszta -> pełna ścieżka
      let loc = rel === "index.html" ? "/" : rel.endsWith("/index.html") ? "/" + rel.slice(0, -"index.html".length) : "/" + rel;
      const stat = fs.statSync(path.join(dir, e.name));
      urls.push({ loc: DOMAIN + loc, lastmod: stat.mtime.toISOString().slice(0, 10) });
    }
  }
}
walk(ROOT);
urls.sort((a, b) => a.loc.localeCompare(b.loc));

const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map(u => `  <url><loc>${u.loc}</loc><lastmod>${u.lastmod}</lastmod></url>`).join("\n")}
</urlset>
`;
fs.writeFileSync("sitemap.xml", xml);
console.log(`sitemap.xml: ${urls.length} URLi`);

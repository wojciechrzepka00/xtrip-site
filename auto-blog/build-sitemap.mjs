// Generuje kompletny sitemap.xml ze wszystkich publicznych stron .html
// (strona główna + wersje językowe + blog + artykuły). Uruchamiane po generacji.
import fs from "fs";
import path from "path";
import { execFileSync } from "child_process";

const DOMAIN = "https://krakow-transfers.com";
const ROOT = process.cwd();
const SKIP = new Set(["payments-backend", "auto-blog", "google-calendar-system", ".github", "node_modules", ".git"]);
const SKIP_FILES = new Set(["index-preview.html"]);

// lastmod: data z treści (JSON-LD dateModified artykułu), potem data ostatniego commita pliku w git,
// na końcu mtime. Sam mtime w GitHub Actions = czas checkoutu (codziennie "dziś"), więc Google by go ignorował.
function lastmodOf(abs, rel) {
  const html = fs.readFileSync(abs, "utf-8");
  const m = html.match(/"dateModified":\s*"(\d{4}-\d{2}-\d{2})/);
  if (m) return m[1];
  try {
    const dirty = execFileSync("git", ["status", "--porcelain", "--", rel], { cwd: ROOT, encoding: "utf-8" }).trim();
    if (!dirty) {
      const d = execFileSync("git", ["log", "-1", "--format=%cs", "--", rel], { cwd: ROOT, encoding: "utf-8" }).trim();
      if (d) return d;
    }
  } catch {}
  return fs.statSync(abs).mtime.toISOString().slice(0, 10);
}

const urls = [];
function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.isDirectory()) {
      if (SKIP.has(e.name)) continue;
      walk(path.join(dir, e.name));
    } else if (e.isFile() && e.name.endsWith(".html") && !SKIP_FILES.has(e.name)
               && !fs.readFileSync(path.join(dir, e.name), "utf8").slice(0, 200).includes("<!--redirect-->")) {
      let rel = path.relative(ROOT, path.join(dir, e.name)).split(path.sep).join("/");
      // index.html -> katalog; reszta -> pełna ścieżka
      let loc = rel === "index.html" ? "/" : rel.endsWith("/index.html") ? "/" + rel.slice(0, -"index.html".length) : "/" + rel;
      urls.push({ loc: DOMAIN + loc, lastmod: lastmodOf(path.join(dir, e.name), rel) });
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

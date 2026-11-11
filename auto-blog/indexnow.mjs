// Tells Bing/Yandex/Seznam (IndexNow) about pages changed in the last commit.
// Usage: node scripts/indexnow.mjs [hours]   (default 26: everything committed in the last 26 h,
// which the server has already pulled by the time the daily blog run calls this)
import { execSync } from "node:child_process";
const KEY = "39462a3328c74c6f903348bd8ec2afcd";
const HOST = "krakow-transfers.com";
const hours = Number(process.argv[2] || 26);
let files = [];
try { files = execSync(`git log --since="${hours} hours ago" --name-only --format=`, { encoding: "utf8" }).split("\n"); } catch { process.exit(0); }
const urls = [...new Set(files.filter((f) => f.endsWith(".html") && !f.startsWith("google") && !f.startsWith("index-preview") && !/^(auto-blog|payments-backend|google-calendar-system)\//.test(f) && !f.includes("/_"))
  .map((f) => `https://${HOST}/${f.replace(/(^|\/)index\.html$/, "$1")}`))].slice(0, 10000);
if (!urls.length) { console.log("IndexNow: nothing changed"); process.exit(0); }
const res = await fetch("https://api.indexnow.org/indexnow", {
  method: "POST", headers: { "content-type": "application/json; charset=utf-8" },
  body: JSON.stringify({ host: HOST, key: KEY, keyLocation: `https://${HOST}/${KEY}.txt`, urlList: urls }),
}).catch((e) => ({ status: String(e) }));
console.log(`IndexNow: ${urls.length} URLs → ${res.status}`);

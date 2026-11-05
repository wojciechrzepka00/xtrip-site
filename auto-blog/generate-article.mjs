// generate-article.mjs — automatyczny blog krakow-transfers.com (9 języków)
//
// Każde uruchomienie (GitHub Actions, codziennie):
//   1. NAPRAWA: czyta całą historię bloga (posts.json + ręczne artykuły z blog.html)
//      i dorabia brakujące lub uszkodzone wersje językowe istniejących artykułów
//      (maks. REPAIR_MAX na jedno uruchomienie).
//   2. NOWY ARTYKUŁ: tylko jeśli od ostatniego minęły co najmniej NEW_EVERY_DAYS dni.
//      Temat wymyśla model na podstawie PEŁNEJ listy dotychczasowych tytułów, a skrypt
//      dodatkowo sam sprawdza podobieństwo do każdego artykułu w historii. Jeśli nie da
//      się znaleźć tematu bez powtórki — nie publikuje nic (nigdy duplikatu).
//
// Zmienne: ANTHROPIC_API_KEY (sekret), BLOG_MODEL (opcjonalnie), BLOG_FORCE_NEW=1
// (nowy artykuł niezależnie od odstępu), BLOG_MOCK=1 (test bez API, nic nie kosztuje).

import fs from "fs";
import path from "path";

const LANGS = [
  { code: "pl", name: "polski",     dir: "ltr" },
  { code: "en", name: "angielski",  dir: "ltr" },
  { code: "de", name: "niemiecki",  dir: "ltr" },
  { code: "fr", name: "francuski",  dir: "ltr" },
  { code: "it", name: "włoski",     dir: "ltr" },
  { code: "es", name: "hiszpański", dir: "ltr" },
  { code: "mt", name: "maltański",  dir: "ltr" },
  { code: "uk", name: "ukraiński",  dir: "ltr" },
  { code: "ar", name: "arabski",    dir: "rtl" },
];
const LATIN_SLUG = new Set(["pl", "en", "de", "fr", "it", "es", "mt"]); // uk/ar: slug z angielskiego tytułu

const MODEL = process.env.BLOG_MODEL || "claude-sonnet-5";
const MOCK = process.env.BLOG_MOCK === "1";
const FORCE_NEW = process.env.BLOG_FORCE_NEW === "1";
const NEW_EVERY_DAYS = Number(process.env.BLOG_NEW_EVERY_DAYS || 3);
const REPAIR_MAX = Number(process.env.BLOG_REPAIR_MAX || 9);
const MIN_WORDS = 300;          // nowy artykuł: minimum słów
const BROKEN_WORDS = 150;       // istniejący artykuł poniżej tego = uszkodzony, do naprawy
const DOMAIN = "https://krakow-transfers.com";
const TODAY = new Date().toISOString().slice(0, 10);

const COMPANY = `Firma: "Katowice Pyrzowice Airport Transfers" (krakow-transfers.com) — prywatne i grupowe transfery z lotniska
Katowice-Pyrzowice (KTW) do Krakowa i Zakopanego (i z powrotem), 20 lat doświadczenia. Flota: Chrysler Pacifica, Mercedes Vito,
Mercedes Sprinter, autobusy. Kierowca czeka w hali przylotów z tabliczką z nazwiskiem.`;

// ---------- pomocnicze ----------
const slugify = (t) => String(t).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
  .replace(/ł/g, "l").replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "").slice(0, 80).replace(/-+$/, "");
const words = (html) => String(html).replace(/<[^>]+>/g, " ").split(/\s+/).filter(Boolean).length;
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
const daysBetween = (a, b) => Math.round((new Date(b) - new Date(a)) / 86400000);

function loadPosts() {
  try { return JSON.parse(fs.readFileSync("posts.json", "utf-8")); } catch { return []; }
}

// ręcznie napisane artykuły (lista w blog.html, poza automatyczną sekcją)
function loadHandmade() {
  const html = fs.readFileSync("blog.html", "utf-8");
  return [...html.matchAll(/<h2><a href="(blog\/[^"]+\.html)">([^<]+)<\/a>/g)].map((m) => ({ url: m[1], title: m[2].trim() }));
}

// ---------- wykrywanie powtórek tematu ----------
const STOP = new Set(`a i w we z ze na do od po o u za przy dla czy jak co gdy kiedy gdzie ile czego jest sa to ten ta te
  ktory ktora ktore oraz lub albo bez nad pod przez jego sie ich czym wszystko wszystkie najwazniejsze praktyczny praktyczne
  przewodnik poradnik wskazowki porady informacje warto wiedziec transfer transferu transfery transferem lotnisko lotniska
  lotnisku lotniskowy lotniskowe lotniskowego pyrzowice pyrzowicach pyrzowic katowice katowic krakow krakowa krakowie zakopane
  zakopanego zakopanem podroz podrozy podrozowanie trasa trasie droga drodze`.split(/\s+/));
function stems(title) {
  return new Set(String(title).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ł/g, "l")
    .replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter((w) => w.length > 2 && !STOP.has(w)).map((w) => w.slice(0, 5)));
}
function closestInHistory(title, history) {
  const A = stems(title);
  let best = { score: 0, title: "" };
  if (!A.size) return { score: 1, title: "(temat zbyt ogólny)" };
  for (const h of history) {
    const B = stems(h);
    if (!B.size) continue;
    const inter = [...A].filter((w) => B.has(w)).length;
    const score = inter / Math.min(A.size, B.size);
    if (score > best.score) best = { score, title: h };
  }
  return best;
}

// ---------- API ----------
async function callTool(system, user, tool, maxTokens = 3000) {
  let lastErr;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "content-type": "application/json", "x-api-key": process.env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01" },
        body: JSON.stringify({ model: MODEL, max_tokens: maxTokens, system, messages: user,
          tools: [tool], tool_choice: { type: "tool", name: tool.name } }),
      });
      if (!res.ok) throw new Error(`API ${res.status}: ${(await res.text()).slice(0, 300)}`);
      const data = await res.json();
      const block = (data.content || []).find((c) => c.type === "tool_use");
      if (!block) throw new Error("brak odpowiedzi narzędzia");
      return { input: block.input, content: data.content, id: block.id };
    } catch (e) {
      lastErr = e;
      if (/API 4(00|01|03|04)/.test(e.message)) break;   // błędy konfiguracji / środków — nie ma sensu ponawiać
      await new Promise((r) => setTimeout(r, 5000 * attempt));
    }
  }
  throw lastErr;
}

const TOPIC_TOOL = {
  name: "propose_topic",
  description: "Zaproponuj jeden nowy temat artykułu.",
  input_schema: { type: "object", properties: {
    topic_pl: { type: "string", description: "tytuł/temat po polsku, 40–90 znaków" },
    closest_existing: { type: "string", description: "najbardziej podobny istniejący tytuł z listy i czym nowy temat się od niego różni" },
  }, required: ["topic_pl", "closest_existing"] },
};
const ARTICLE_TOOL = {
  name: "publish_article",
  description: "Opublikuj artykuł.",
  input_schema: { type: "object", properties: {
    title: { type: "string", description: "tytuł w języku docelowym, czysty tekst" },
    title_en: { type: "string", description: "ten sam tytuł po angielsku (do adresu URL)" },
    body_html: { type: "string", description: "treść HTML: tylko <p>, <h3>, <ul>, <li>, <strong>; bez H1" },
  }, required: ["title", "title_en", "body_html"] },
};

async function proposeTopic(history) {
  if (MOCK) return `Test automatu ${Date.now().toString(36)} — sprawdzenie publikacji`;
  const system = `Planujesz bloga firmy transferowej. ${COMPANY}
Czytelnicy: turyści i biznes przylatujący do Katowic-Pyrzowic. Tematy muszą być praktyczne i związane z przylotem,
dojazdem do Krakowa/Zakopanego, okolicą, sezonami, grupami, rodzinami, biznesem. Nie wymyślaj cen ani faktów o lotnisku.`;
  const list = history.map((t) => `- ${t}`).join("\n");
  const messages = [{ role: "user", content:
    `Oto PEŁNA historia bloga — każdy artykuł opublikowany od początku (${history.length}):\n${list}\n\n` +
    `Zaproponuj JEDEN nowy temat, który NIE pokrywa się z żadnym z powyższych — ani dosłownie, ani innymi słowami, ani jako ` +
    `ten sam problem z innej strony. Wybierz zupełnie inny obszar niż istniejące. Odpowiedz narzędziem propose_topic.` }];
  for (let attempt = 1; attempt <= 5; attempt++) {
    const r = await callTool(system, messages, TOPIC_TOOL, 600);
    const topic = String(r.input.topic_pl || "").trim();
    const twin = closestInHistory(topic, history);
    const exact = history.some((h) => h.toLowerCase() === topic.toLowerCase());
    if (topic.length >= 25 && !exact && twin.score < 0.5) {
      console.log(`Temat: "${topic}" (najbliższy w historii: "${twin.title}", podobieństwo ${twin.score.toFixed(2)})`);
      return topic;
    }
    console.log(`  propozycja ${attempt} odrzucona: "${topic}" ~ "${twin.title}" (${twin.score.toFixed(2)})`);
    messages.push({ role: "assistant", content: r.content });
    messages.push({ role: "user", content: [{ type: "tool_result", tool_use_id: r.id, is_error: true,
      content: `Za podobny do istniejącego artykułu "${twin.title}". Wybierz zupełnie inny obszar tematyczny i zaproponuj ponownie.` }] });
  }
  return null;
}

async function writeArticle(topic, lang) {
  if (MOCK) {
    const p = `<p>To jest testowy akapit automatu bloga w języku ${lang.name}, pisany bez API. </p>`.repeat(40);
    return { title: `[${lang.code}] ${topic}`, title_en: `Test ${topic}`, body: p };
  }
  const system = `Piszesz artykuły na blog firmy. ${COMPANY}
Zasady: praktycznie i konkretnie, 450–700 słów, krótkie akapity, śródtytuły <h3>. Nie wymyślaj cen, godzin, numerów terminali ani
zmian na lotnisku — jeśli coś się zmienia, odeślij do oficjalnej strony. Bez emoji. Nie dodawaj H1 ani tytułu na początku treści.`;
  const user = [{ role: "user", content:
    `Temat (opisany po polsku): "${topic}".\nNapisz CAŁY artykuł (tytuł i treść) w języku: ${lang.name}. ` +
    `Odpowiedz narzędziem publish_article.` }];
  for (let attempt = 1; attempt <= 2; attempt++) {
    const r = await callTool(system, user, ARTICLE_TOOL, 4000);
    const title = String(r.input.title || "").replace(/<[^>]+>/g, "").trim();
    const body = String(r.input.body_html || "").replace(/<\/?(h1|h2|script|style|iframe)[^>]*>/gi, "").trim();
    const problems = [];
    if (title.length < 10) problems.push("brak tytułu");
    if (lang.code !== "pl" && title.toLowerCase() === topic.toLowerCase()) problems.push("tytuł nieprzetłumaczony");
    if (!/<p>/i.test(body)) problems.push("brak akapitów");
    if (words(body) < MIN_WORDS) problems.push(`za krótki (${words(body)} słów)`);
    if (!problems.length) return { title, title_en: String(r.input.title_en || title), body };
    console.log(`  [${lang.code}] próba ${attempt} odrzucona: ${problems.join("; ")}`);
  }
  throw new Error("nie udało się napisać poprawnego artykułu");
}

// ---------- pliki ----------
const OG_LOCALES = { pl: "pl_PL", en: "en_US", de: "de_DE", fr: "fr_FR", it: "it_IT", es: "es_ES", mt: "mt_MT", uk: "uk_UA", ar: "ar_AR" };
const TEMPLATE = (title, body, lang, slug, hreflang = "") => {
  const url = `${DOMAIN}/blog/${lang.code}/${slug}.html`;
  const desc = body.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().slice(0, 155);
  return `<!DOCTYPE html>
<html lang="${lang.code}"${lang.dir === "rtl" ? ' dir="rtl"' : ""}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(title)} | Katowice Pyrzowice Airport Transfers</title>
<meta name="description" content="${esc(desc)}">
<link rel="canonical" href="${url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Katowice Pyrzowice Airport Transfers">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:url" content="${url}">
<meta property="og:image" content="${DOMAIN}/images/vito.jpg">
<meta property="og:locale" content="${OG_LOCALES[lang.code] || "en_US"}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(desc)}">
<meta name="twitter:image" content="${DOMAIN}/images/vito.jpg">
${hreflang}
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  body{ font-family:'Inter',sans-serif; background:#FAF8F2; color:#13161B; margin:0; line-height:1.7; }
  header{ background:#0F2038; padding:20px 28px; }
  header a{ color:#EEEAE1; text-decoration:none; font-family:'Fraunces',serif; font-weight:600; font-size:16px; }
  .wrap{ max-width:720px; margin:0 auto; padding:50px 24px 80px; }
  h1{ font-family:'Fraunces',serif; font-size:30px; margin:0 0 22px; color:#0F2038; }
  h3{ font-family:'Fraunces',serif; font-size:21px; margin:30px 0 12px; color:#0F2038; }
  p, li{ font-size:16px; color:#333; margin:0 0 18px; }
  .back{ display:inline-block; margin-bottom:28px; font-size:13px; color:#C4872F; text-decoration:none; }
</style>
</head>
<body>
<header><a href="../../index.html">← KATOWICE PYRZOWICE AIRPORT TRANSFERS</a></header>
<div class="wrap">
  <a class="back" href="../../blog.html">← ${lang.code === "pl" ? "Wszystkie artykuły" : "All articles"}</a>
  <h1>${esc(title)}</h1>
  ${body}
</div>
</body>
</html>`;
};

function uniqueSlug(lang, title, titleEn) {
  const base = (LATIN_SLUG.has(lang.code) ? slugify(title) : "") || slugify(titleEn) || "article";
  let slug = `${base}-${lang.code}`, n = 2;
  while (fs.existsSync(path.join("blog", lang.code, `${slug}.html`))) slug = `${base}-${lang.code}-${n++}`;
  return slug;
}

function hreflangBlock(group) {
  const en = group.find((p) => p.lang === "en") || group[0];
  return group.map((p) => `<link rel="alternate" hreflang="${p.lang}" href="${DOMAIN}/${p.url}">`).join("\n")
    + (en ? `\n<link rel="alternate" hreflang="x-default" href="${DOMAIN}/${en.url}">` : "");
}

// po każdej zmianie w grupie: wszystkie wersje językowe dostają aktualne, wzajemne linki hreflang
function relinkGroup(group) {
  const block = hreflangBlock(group);
  for (const p of group) {
    if (!fs.existsSync(p.url)) continue;
    let s = fs.readFileSync(p.url, "utf-8");
    s = s.replace(/(<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n?)+/g, "");
    s = s.replace(/(<meta name="twitter:image"[^>]*>\n)/, `$1${block}\n`);
    fs.writeFileSync(p.url, s);
  }
}

function brokenReason(p, topicKey) {
  if (!fs.existsSync(p.url)) return "brak pliku";
  const s = fs.readFileSync(p.url, "utf-8");
  const body = (s.split(/<\/h1>/)[1] || "").replace(/<\/div>[\s\S]*$/, "");
  if (words(body) < BROKEN_WORDS) return `pusta/za krótka treść (${words(body)} słów)`;
  if (p.lang !== "pl" && p.title.trim().toLowerCase() === topicKey.trim().toLowerCase()) return "tytuł nieprzetłumaczony";
  return "";
}

function addVersion(posts, topicKey, date, lang, art) {
  const slug = uniqueSlug(lang, art.title, art.title_en);
  const url = `blog/${lang.code}/${slug}.html`;
  fs.mkdirSync(path.join("blog", lang.code), { recursive: true });
  fs.writeFileSync(url, TEMPLATE(art.title, art.body, lang, slug));
  posts.push({ title: art.title, topicKey, lang: lang.code, url,
    meta: art.body.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().slice(0, 140), date });
  console.log(`  [${lang.code}] OK: ${art.title} -> ${url}`);
}

// ---------- główny przebieg ----------
async function main() {
  if (!MOCK && !process.env.ANTHROPIC_API_KEY) throw new Error("Brak ANTHROPIC_API_KEY (GitHub → Settings → Secrets → Actions).");
  let posts = loadPosts();
  const handmade = loadHandmade();
  let failures = 0;

  // 1) NAPRAWA brakujących / uszkodzonych wersji językowych
  const groups = new Map();
  for (const p of posts) { if (!groups.has(p.topicKey)) groups.set(p.topicKey, []); groups.get(p.topicKey).push(p); }
  let repairs = 0;
  for (const [topicKey, group] of groups) {
    const date = group.map((p) => p.date).sort()[0];
    let changed = false;
    for (const lang of LANGS) {
      if (repairs >= REPAIR_MAX) break;
      const existing = group.filter((p) => p.lang === lang.code);
      const ok = existing.filter((p) => !brokenReason(p, topicKey));
      if (ok.length) continue;
      const why = existing.length ? brokenReason(existing[0], topicKey) : "brak wersji";
      console.log(`Naprawa: "${topicKey}" [${lang.code}] — ${why}`);
      repairs++;
      try {
        const art = await writeArticle(topicKey, lang);
        for (const bad of existing) { if (fs.existsSync(bad.url)) fs.unlinkSync(bad.url); }
        posts = posts.filter((p) => !existing.includes(p));
        addVersion(posts, topicKey, date, lang, art);
        changed = true;
      } catch (e) { failures++; console.error(`  [${lang.code}] BŁĄD: ${e.message}`); }
    }
    if (changed) relinkGroup(posts.filter((p) => p.topicKey === topicKey));
  }
  if (!repairs) console.log("Naprawa: wszystkie artykuły mają komplet poprawnych wersji językowych.");

  // 2) NOWY ARTYKUŁ (co NEW_EVERY_DAYS dni)
  const last = posts.map((p) => p.date).sort().pop();
  const due = FORCE_NEW || !last || daysBetween(last, TODAY) >= NEW_EVERY_DAYS;
  if (!due) {
    console.log(`Nowy artykuł: jeszcze nie (ostatni ${last}, co ${NEW_EVERY_DAYS} dni).`);
  } else {
    const history = [...new Set([
      ...handmade.filter((h) => /^blog\/[^/]+\.html$/.test(h.url)).map((h) => h.title), // ręczne PL
      ...posts.map((p) => p.topicKey),                                                      // wszystkie automatyczne
      ...posts.filter((p) => p.lang === "en").map((p) => p.title),
      ...handmade.filter((h) => /^blog\/en\//.test(h.url)).map((h) => h.title),
    ])];
    const topic = await proposeTopic(history);
    if (!topic) {
      failures++;
      console.error("Nie znaleziono tematu bez powtórki — dziś bez nowego artykułu (żadnych duplikatów).");
    } else {
      let made = 0;
      for (const lang of LANGS) {
        try { addVersion(posts, topic, TODAY, lang, await writeArticle(topic, lang)); made++; }
        catch (e) { failures++; console.error(`  [${lang.code}] BŁĄD: ${e.message} (uzupełni się przy następnym uruchomieniu)`); }
      }
      if (made) relinkGroup(posts.filter((p) => p.topicKey === topic));
    }
  }

  posts.sort((a, b) => (b.date || "").localeCompare(a.date || ""));
  fs.writeFileSync("posts.json", JSON.stringify(posts, null, 2));
  console.log(`Gotowe — posts.json: ${posts.length} wpisów.`);
  if (failures) { console.error(`Uwaga: ${failures} problem(ów) — szczegóły wyżej.`); process.exitCode = 1; }
}

main().catch((err) => { console.error(err.message || err); process.exit(1); });

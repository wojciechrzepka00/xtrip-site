// generate-article.mjs
// Generuje JEDEN temat, ale od razu W KAŻDYM z 9 języków przy każdym uruchomieniu
// (nie rotację "jeden język na raz" jak wcześniej) — jako osobne, indeksowalne
// podstrony w blog/{lang}/, i dopisuje 9 wpisów do posts.json.
// Wymaga zmiennej środowiskowej ANTHROPIC_API_KEY (sekret w GitHub Actions).
//
// UWAGA O KOSZTACH: to wywołuje API Anthropic 9 razy przy KAŻDYM uruchomieniu
// (raz na język), zamiast 1 raz jak w poprzedniej wersji skryptu. Przy stawce
// workflow co 3 dni to ok. 9 artykułów / 3 dni = 3 artykuły dziennie łącznie
// (po jednym w każdym języku co 3 dni). Sprawdź limity/koszty na koncie
// console.anthropic.com, zanim zostawisz to długo działające bez nadzoru.
//
// Kolejność języków w tablicy LANGS nie ma już znaczenia dla priorytetu —
// wszystkie powstają w tym samym uruchomieniu. Angielski jest pierwszy na
// liście czysto porządkowo (najważniejszy rynek), ale wszystkie 9 i tak
// powstają razem.

import fs from "fs";
import path from "path";

const LANGS = [
  { code: "en", name: "angielski",  dir: "ltr" },
  { code: "de", name: "niemiecki",  dir: "ltr" },
  { code: "pl", name: "polski",     dir: "ltr" },
  { code: "fr", name: "francuski",  dir: "ltr" },
  { code: "it", name: "włoski",     dir: "ltr" },
  { code: "es", name: "hiszpański", dir: "ltr" },
  { code: "mt", name: "maltański",  dir: "ltr" },
  { code: "uk", name: "ukraiński",  dir: "ltr" },
  { code: "ar", name: "arabski",    dir: "rtl" },
];

// Tematy bazowe (po polsku — model pisze od razu w docelowym języku, nie tłumaczy dosłownie tytułu)
const TOPICS = [
  "Bezpieczeństwo na drodze zimą w rejonie Tatr",
  "Jak zaplanować transfer, gdy lecisz z przesiadką",
  "Podróżowanie ze zwierzęciem domowym przez lotnisko",
  "Najczęstsze pytania klientów biznesowych o transfer lotniskowy",
  "Jak wygląda odbiór grupowy przy dużych wydarzeniach sportowych",
  "Sezon urlopowy na Pyrzowicach — kiedy jest największy ruch",
  "Co spakować na weekend w Zakopanem",
  "Jak przygotować się do transferu z małym dzieckiem w foteliku",
  "Dlaczego warto rezerwować transfer z wyprzedzeniem",
  "Zmiana terminala na Pyrzowicach — co to oznacza dla pasażerów",
  "Podróż na narty do Zakopanego z zagranicy — praktyczny przewodnik",
  "Kraków dla turystów zagranicznych — pierwsze kroki po przylocie",
];

function slugify(text) {
  return text
    .toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function loadPosts() {
  try { return JSON.parse(fs.readFileSync("posts.json", "utf-8")); } catch (e) { return []; }
}

function pickTopic(posts) {
  // Temat uznajemy za "użyty", jeśli powstał w KTÓRYMKOLWIEK języku — unikamy powtórek między turami
  const usedTopics = new Set(posts.map(p => p.topicKey));
  const unused = TOPICS.filter(t => !usedTopics.has(t));
  const pool = unused.length ? unused : TOPICS;
  return pool[Math.floor(Math.random() * pool.length)];
}

async function generateArticle(topic, lang) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": process.env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-sonnet-5",
      max_tokens: 1400,
      messages: [
        {
          role: "user",
          content: `Napisz artykuł na blog firmy transportowej "Katowice Pyrzowice Airport Transfers" (transfery z lotniska Katowice-Pyrzowice do Krakowa i Zakopanego, flota: Chrysler Pacifica, Mercedes Vito, Mercedes Sprinter, autobusy). Temat (opisany po polsku, ale NAPISZ CAŁY ARTYKUŁ w języku: ${lang.name}): "${topic}". Artykuł: praktyczny, konkretny, 400-600 słów, w języku ${lang.name}, HTML (akapity <p>, ewentualnie <h3>). Nie wymyślaj konkretnych cen. Nie dodawaj tytułu H1. Zwróć TYLKO: pierwsza linia = przetłumaczony tytuł artykułu (czysty tekst, bez HTML), druga linia dokładnie "---", a dalej treść HTML w języku ${lang.name}.`,
        },
      ],
    }),
  });
  const data = await res.json();
  const text = (data.content?.map(b => b.text || "").join("\n") || "").trim();
  const sepIndex = text.indexOf("---");
  if (sepIndex === -1) {
    return { translatedTitle: topic, body: text };
  }
  const translatedTitle = text.slice(0, sepIndex).replace(/\n/g, " ").trim();
  const body = text.slice(sepIndex + 3).trim();
  return { translatedTitle, body };
}

const TEMPLATE = (title, body, lang) => `<!DOCTYPE html>
<html lang="${lang.code}"${lang.dir === "rtl" ? ' dir="rtl"' : ""}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${title} | Katowice Pyrzowice Airport Transfers</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  body{ font-family:'Inter',sans-serif; background:#FAF8F2; color:#13161B; margin:0; line-height:1.7; }
  header{ background:#0F2038; padding:20px 28px; }
  header a{ color:#EEEAE1; text-decoration:none; font-family:'Fraunces',serif; font-weight:600; font-size:16px; }
  .wrap{ max-width:720px; margin:0 auto; padding:50px 24px 80px; }
  h1{ font-family:'Fraunces',serif; font-size:30px; margin:0 0 22px; color:#0F2038; }
  p{ font-size:16px; color:#333; margin:0 0 18px; }
  .back{ display:inline-block; margin-bottom:28px; font-size:13px; color:#C4872F; text-decoration:none; }
</style>
</head>
<body>
<header><a href="../../${lang.code === 'pl' ? '' : ''}index.html">← KATOWICE PYRZOWICE AIRPORT TRANSFERS</a></header>
<div class="wrap">
  <a class="back" href="../../blog.html">← ${lang.code === 'pl' ? 'Wszystkie artykuły' : 'All articles'}</a>
  <h1>${title}</h1>
  ${body}
</div>
</body>
</html>`;

async function main() {
  const posts = loadPosts();
  const topic = pickTopic(posts);

  console.log(`Temat tej tury: "${topic}" — generuję w ${LANGS.length} językach...`);

  for (const lang of LANGS) {
    try {
      const { translatedTitle, body } = await generateArticle(topic, lang);
      const slug = slugify(translatedTitle || topic) + "-" + Date.now().toString().slice(-5);
      const dir = path.join("blog", lang.code);
      fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(path.join(dir, `${slug}.html`), TEMPLATE(translatedTitle, body, lang));

      posts.unshift({
        title: translatedTitle,
        topicKey: topic,
        lang: lang.code,
        url: `blog/${lang.code}/${slug}.html`,
        meta: "Nowy artykuł dodany automatycznie.",
        date: new Date().toISOString().slice(0, 10),
      });
      console.log(`  [${lang.code}] OK: ${translatedTitle} -> ${slug}`);
    } catch (err) {
      console.error(`  [${lang.code}] BŁĄD:`, err.message);
      // Kontynuujemy z pozostałymi językami, nawet jeśli jeden się nie uda
    }
  }

  fs.writeFileSync("posts.json", JSON.stringify(posts, null, 2));
  console.log("Gotowe — zapisano posts.json");
}

main().catch(err => { console.error(err); process.exit(1); });

# Jednorazowa (powtarzalna) poprawka SEO ręcznie pisanych artykułów bloga (spoza posts.json).
# Uruchom z katalogu repo: python3 auto-blog/fix-handmade-posts.py
# Przepisuje tylko <head> (tytuł, jeden opis, canonical, OG, hreflang, JSON-LD) i link w nagłówku; treść zostaje.
import json, os, re, glob, html, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
DOMAIN = "https://krakow-transfers.com"
BRAND = "Kraków Transfers"
TITLE_MAX = 62
ORG = json.load(open("auto-blog/org.json", encoding="utf-8"))
SEO_TITLES = json.load(open("auto-blog/seo-titles.json", encoding="utf-8"))
OG = {"pl": "pl_PL", "en": "en_US", "de": "de_DE", "fr": "fr_FR", "it": "it_IT", "es": "es_ES", "mt": "mt_MT", "uk": "uk_UA", "ar": "ar_AR"}
HOME_NAME = {"pl": "Strona główna", "en": "Home", "de": "Startseite", "fr": "Accueil", "it": "Home", "es": "Inicio", "mt": "Paġna ewlenija", "uk": "Головна", "ar": "الرئيسية"}
ORDER = ["pl", "en", "de", "fr", "it", "es", "mt", "uk", "ar"]
# wersje językowe tych samych ręcznych artykułów (kolejność jak ORDER)
GROUPS = [
 ["blog/jak-dojechac-pyrzowice-krakow.html", "blog/en/how-to-get-from-pyrzowice-to-krakow.html", "blog/de/wie-komme-ich-pyrzowice-krakau.html", "blog/fr/comment-aller-pyrzowice-cracovie.html", "blog/it/come-arrivare-pyrzowice-cracovia.html", "blog/es/como-llegar-pyrzowice-cracovia.html", "blog/mt/kif-tasal-pyrzowice-krakovja.html", "blog/uk/yak-distatysya-pyzhovytsi-krakiv.html", "blog/ar/kayfa-tasil-pyrzowice-krakow.html"],
 ["blog/transfer-biznesowy-pyrzowice.html", "blog/en/business-transfer-pyrzowice-en.html", "blog/de/geschaeftstransfer-pyrzowice-de.html", "blog/fr/transfert-affaires-pyrzowice-fr.html", "blog/it/transfer-business-pyrzowice-it.html", "blog/es/traslado-negocios-pyrzowice-es.html", "blog/mt/trasferiment-negozju-pyrzowice-mt.html", "blog/uk/biznes-transfer-pyzhovytsi-uk.html", "blog/ar/naql-aamal-pyrzowice-ar.html"],
 ["blog/ile-trwa-droga-pyrzowice-zakopane.html", "blog/en/how-long-pyrzowice-zakopane-en.html", "blog/de/wie-lange-pyrzowice-zakopane-de.html", "blog/fr/duree-trajet-pyrzowice-zakopane-fr.html", "blog/it/quanto-dura-viaggio-pyrzowice-zakopane-it.html", "blog/es/cuanto-dura-viaje-pyrzowice-zakopane-es.html", "blog/mt/kemm-idum-vjagg-pyrzowice-zakopane-mt.html", "blog/uk/skilky-tryvaye-doroga-pyzhovytsi-zakopane-uk.html", "blog/ar/kam-yastaghriq-tariq-pyrzowice-zakopane-ar.html"],
 ["blog/ile-bagazu-transfer-lotniskowy.html", "blog/en/how-much-luggage-airport-transfer-en.html", "blog/de/wieviel-gepaeck-transfer-de.html", "blog/fr/combien-bagages-transfert-aeroport-fr.html", "blog/it/quanti-bagagli-transfer-aeroportuale-it.html", "blog/es/cuanto-equipaje-traslado-aeropuerto-es.html", "blog/mt/kemm-bagalji-trasferiment-ajruport-mt.html", "blog/uk/skilky-bagazhu-transfer-aeroport-uk.html", "blog/ar/kam-amtiaa-naql-matar-ar.html"],
 ["blog/zakopane-poza-sezonem.html", "blog/en/zakopane-off-season-en.html", "blog/de/zakopane-nebensaison-de.html", "blog/fr/zakopane-hors-saison-fr.html", "blog/it/zakopane-bassa-stagione-it.html", "blog/es/zakopane-temporada-baja-es.html", "blog/mt/zakopane-barra-stagun-mt.html", "blog/uk/zakopane-poza-sezonom-uk.html", "blog/ar/zakopane-khar-almawsim-ar.html"],
 ["blog/wieliczka-auschwitz-jednodniowe.html", "blog/en/wieliczka-auschwitz-day-trips-en.html", "blog/de/wieliczka-auschwitz-tagesausfluege-de.html", "blog/fr/wieliczka-auschwitz-excursions-fr.html", "blog/it/wieliczka-auschwitz-gite-it.html", "blog/es/wieliczka-auschwitz-excursiones-es.html", "blog/mt/wieliczka-auschwitz-vjaggi-mt.html", "blog/uk/velychka-auschwitz-ekskursii-uk.html", "blog/ar/wieliczka-auschwitz-rihlat-ar.html"],
]
GROUP_OF = {u: g for g in GROUPS for u in g}

def plain(h): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()

def seo_title(h1, rel):
    B = " | " + BRAND
    wb = lambda x: x + B if len(x + B) <= TITLE_MAX else x
    if rel in SEO_TITLES: return wb(SEO_TITLES[rel])
    if len(h1 + B) <= TITLE_MAX: return h1 + B
    m = re.match(r"^(.{20,}?)(\s[—–-]\s|:\s|\?\s)", h1)
    head = (m.group(1) + ("?" if m.group(2).startswith("?") else "")).strip() if m else None
    if head and len(head) >= 30 and len(head + B) <= TITLE_MAX: return head + B
    if len(h1) <= TITLE_MAX: return h1
    if head and len(head + B) <= TITLE_MAX: return head + B
    if head and 30 <= len(head) <= TITLE_MAX: return head
    return re.sub(r"\s+\S*$", "", h1[:58]) + "…"

def sentences(t): return [x.strip() for x in re.findall(r"[^.!?؟]+[.!?؟]+(?:\s|$)", t)] or [t]

def meta_desc(cands, body_text):
    good = [c for c in cands if 120 <= len(c) <= 160]
    if good: return max(good, key=len)
    for base in sorted(cands, key=len, reverse=True) + [""]:
        out = base
        for s in sentences(body_text):
            if s in out: continue
            nxt = (out + " " + s).strip()
            if len(nxt) > 160: break
            out = nxt
            if len(out) >= 150: break
        if 120 <= len(out) <= 160: return out
    return re.sub(r"[,;:—–-]$", "", re.sub(r"\s+\S*$", "", body_text[:157])) + "…"

def git_date(rel, first):
    args = ["git", "log", "--format=%cs"] + (["--diff-filter=A"] if first else ["-1"]) + ["--", rel]
    out = subprocess.run(args, capture_output=True, text=True).stdout.split()
    return (out[-1] if first else out[0]) if out else None

def lang_of(rel):
    parts = rel.split("/")
    return parts[1] if len(parts) == 3 else "pl"

def url_of(rel): return DOMAIN + "/" + rel
def J(o): return json.dumps(o, ensure_ascii=False).replace("</", "<\\/")

auto = {p["url"] for p in json.load(open("posts.json", encoding="utf-8"))}
files = sorted(set(glob.glob("blog/**/*.html", recursive=True)) - auto)
n = 0
for rel in files:
    s = open(rel, encoding="utf-8").read()
    lang = lang_of(rel)
    head, body = s.split("</head>", 1)
    h1 = plain(re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S).group(1))
    descs = [html.unescape(x).strip() for x in re.findall(r'<meta name="description" content="([^"]*)"', head)]
    content = body.split("</h1>", 1)[1]
    content = re.split(r'<div class="(?:cta|routes-box)"', content)[0]
    text = plain(content)
    desc = meta_desc(descs, text)
    title = seo_title(h1, rel)
    url = url_of(rel)
    published = git_date(rel, True) or "2026-09-01"
    modified = git_date(rel, False) or published
    m = re.search(r'"datePublished":\s*"([0-9-]+)"', head)  # przy ponownym uruchomieniu zachowaj daty
    if m: published = m.group(1)
    m = re.search(r'"dateModified":\s*"([0-9-]+)"', head)
    if m: modified = m.group(1)
    home = DOMAIN + "/" + ("" if lang == "pl" else lang + "/")
    alts = ""
    if rel in GROUP_OF:
        g = GROUP_OF[rel]
        alts = "\n".join(f'<link rel="alternate" hreflang="{l}" href="{url_of(u)}">' for l, u in zip(ORDER, g))
        alts += f'\n<link rel="alternate" hreflang="x-default" href="{url_of(g[1])}">'
    post = {"@context": "https://schema.org", "@type": "BlogPosting", "@id": url + "#article", "mainEntityOfPage": url,
            "headline": h1, "description": desc, "inLanguage": lang, "image": DOMAIN + "/images/vito.jpg",
            "datePublished": published, "dateModified": modified, "wordCount": len(text.split()),
            "author": {"@type": "Organization", "name": BRAND, "url": DOMAIN + "/"}, "publisher": {"@id": ORG["@id"]},
            "isPartOf": {"@type": "Blog", "@id": DOMAIN + "/blog.html#blog", "name": BRAND + " Blog", "url": DOMAIN + "/blog.html"}}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": HOME_NAME[lang], "item": home},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": DOMAIN + "/blog.html"},
        {"@type": "ListItem", "position": 3, "name": h1, "item": url}]}
    e = lambda x: html.escape(x, quote=True)
    seo = f'''<title>{html.escape(title, quote=False)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{e(h1)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{DOMAIN}/images/vito.jpg">
<meta property="og:locale" content="{OG[lang]}">
<meta property="article:published_time" content="{published}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(h1)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{DOMAIN}/images/vito.jpg">
{alts + chr(10) if alts else ""}<script type="application/ld+json">{J(ORG)}</script>
<script type="application/ld+json">{J(post)}</script>
<script type="application/ld+json">{J(crumbs)}</script>
'''
    h = head
    h = re.sub(r"<!-- SEO:START -->.*?<!-- SEO:END -->\n?", "", h, flags=re.S)
    h = re.sub(r"<title>.*?</title>\n?", "", h, flags=re.S)
    h = re.sub(r'<meta (?:name="description"|property="og:[^"]*"|property="article:[^"]*"|name="twitter:[^"]*")[^>]*>\n?', "", h)
    h = re.sub(r'<link rel="(?:canonical|alternate)"[^>]*>\n?', "", h)
    h = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', "", h, flags=re.S)
    h = re.sub(r'(<meta name="viewport"[^>]*>\n)', lambda m: m.group(1) + "<!-- SEO:START -->\n" + seo + "<!-- SEO:END -->\n", h, count=1)
    home_rel = ("../index.html" if lang == "pl" else f"../../{lang}/") if rel.count("/") == 2 or lang != "pl" else "../index.html"
    if rel.count("/") == 1: home_rel = "../index.html"
    body2 = re.sub(r'<header><a href="[^"]*">', f'<header><a href="{home_rel}">', body, count=1)
    new = h + "</head>" + body2
    if new != s:
        open(rel, "w", encoding="utf-8").write(new); n += 1
print(f"Ręczne artykuły: {len(files)}, zmienione: {n}")

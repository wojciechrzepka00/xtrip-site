# Dopasowanie artykułów bloga do podstron tras (linkowanie wewnętrzne / klastry tematyczne).
# Temat artykułu oceniamy zawsze na POLSKIEJ wersji (link hreflang="pl"), więc wszystkie języki
# tego samego artykułu linkują do tych samych tras. Używane przez link-routes.py i build-routes.py.
import os, re, html, glob, json, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://krakow-transfers.com"
ROUTE_LANGS = ["pl", "en", "de", "fr", "it", "es"]
ORDER = ["kr", "zak", "kz", "krk", "krkzak", "osw", "wiel", "ener", "bialka", "bus"]
DEFAULT = ["kr", "zak", "kz"]

def norm(s):
    s = unicodedata.normalize("NFKD", s.lower().replace("ł", "l"))
    return "".join(c for c in s if not unicodedata.combining(c))

def plain(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()

C = {
    "pyrz": r"pyrzowic|katowic|\bktw\b",
    "krak": r"krakow|krakowa|krakowie",
    "zak": r"zakopan|tatr|podhal|morskie oko|morskiego oka|krupowk|kasprow|gubalowk|termy|termal|bukowin|chocholow|bialk|narci|zakopiank",
    "bal": r"balic",
    "osw": r"auschwitz|oswiecim|birkenau",
    "wiel": r"wielicz|kopalni",
    "ener": r"energyland|zator",
    "bialka": r"bialk",
    "bus": r"przewoz osob|wynajem busa|bus z kierowca|wesel|konferencj|wycieczk[a-z]* szkoln|grup[a-z]* zorganizowan",
}

def concepts(text):
    t = norm(text)
    return {k: len(re.findall(p, t)) for k, p in C.items()}

def _route_scores(c):
    return {
        "kr": (c["pyrz"] + (1 if c["krak"] else 0)) if c["pyrz"] else 0,
        "zak": (c["pyrz"] + c["zak"]) * 0.6 if c["pyrz"] and c["zak"] else 0,
        "kz": c["zak"] * 0.8,
        "krk": c["bal"] * 2,
        "krkzak": c["bal"] * 2 if c["zak"] else 0,
        "osw": c["osw"] * 2,
        "wiel": c["wiel"] * 2,
        "ener": c["ener"] * 2,
        "bialka": c["bialka"] * 2,
        "bus": c["bus"] * 2,
    }

def score(title, body):
    """Wynik dopasowania do tras: trafienia w tytule/adresie liczą się 5x, w treści do limitu."""
    st, sb = _route_scores(concepts(title)), _route_scores(concepts(body))
    return {r: st[r] * 5 + min(sb[r], 6) for r in ORDER}

_cache = {}
def pl_text(path):
    """(tytuł+adres, treść) polskiej wersji artykułu; gdy brak – samego pliku."""
    if path in _cache: return _cache[path]
    h = open(os.path.join(ROOT, path), encoding="utf-8").read()
    m = re.search(r'hreflang="pl" href="' + re.escape(DOMAIN) + r'/([^"]+)"', h)
    src = m.group(1) if m and os.path.exists(os.path.join(ROOT, m.group(1))) else path
    hs = h if src == path else open(os.path.join(ROOT, src), encoding="utf-8").read()
    t = re.search(r"<h1[^>]*>(.*?)</h1>", hs, re.S)
    title = (plain(t.group(1)) if t else "") + " " + os.path.basename(src).replace("-", " ")
    body = re.search(r"</h1>(.*?)<div class=\"routes-box\">", hs, re.S)
    _cache[path] = (title, plain(body.group(1) if body else hs))
    return _cache[path]

def post_scores(path):
    return score(*pl_text(path))

def routes_for(path, n=4):
    s = post_scores(path)
    picked = [r for r in sorted(ORDER, key=lambda r: (-s[r], ORDER.index(r))) if s[r] > 0][:n]
    for r in DEFAULT:
        if len(picked) >= 3: break
        if r not in picked: picked.append(r)
    return picked

def blog_files():
    return sorted(os.path.relpath(f, ROOT) for f in glob.glob(os.path.join(ROOT, "blog", "**", "*.html"), recursive=True) if not is_redirect(f))

def is_redirect(f):
    """Strony-przekierowania (stare adresy usuniętych wpisów, redirects.json) – pomijane przez skrypty."""
    with open(f, encoding="utf-8") as fh: return "<!--redirect-->" in fh.read(200)

def lang_of(path):
    p = path.split("/")
    return p[1] if len(p) == 3 else "pl"

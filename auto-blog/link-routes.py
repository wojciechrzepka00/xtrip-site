# Linkowanie wewnętrzne: w każdym artykule bloga ramka "Zarezerwuj transfer" (routes-box)
# dostaje linki do tras PASUJĄCYCH do tematu (np. Wieliczka -> transfer do Kopalni Soli),
# a nie zawsze te same 3. Uruchom z katalogu repo: python3 auto-blog/link-routes.py
# Powtarzalne – workflow uruchamia go po każdym nowym artykule.
import os, re, sys, html, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import route_topics as RT

spec = importlib.util.spec_from_file_location("br", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build-routes.py"))
BR = importlib.util.module_from_spec(spec); spec.loader.exec_module(BR)
ROOT = RT.ROOT

def h1_of(lang, r):
    h = open(os.path.join(ROOT, BR.path_of(lang, r)), encoding="utf-8").read()
    m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    return html.escape(RT.plain(m.group(1)), quote=False)

LABEL = {l: {r: h1_of(l, r) for r in BR.ROUTES} for l in RT.ROUTE_LANGS}
BOX = re.compile(r'(<div class="routes-box"><p><strong>.*?</strong></p>)<ul>.*?</ul></div>', re.S)

changed = 0
files = RT.blog_files()
for rel in files:
    lang = RT.lang_of(rel)
    tl = lang if lang in RT.ROUTE_LANGS else "en"     # uk/mt/ar -> strony EN
    extra = "" if tl == lang else ' hreflang="en"'
    items = "".join(f'<li><a href="{BR.url_of(tl, r)}"{extra}>{LABEL[tl][r]}</a></li>' for r in RT.routes_for(rel))
    fp = os.path.join(ROOT, rel)
    h = open(fp, encoding="utf-8").read()
    new, n = BOX.subn(lambda m: m.group(1) + "<ul>" + items + "</ul></div>", h, count=1)
    if n and new != h:
        open(fp, "w", encoding="utf-8").write(new); changed += 1
print(f"Linki do tras: zaktualizowano {changed} z {len(files)} artykułów.")

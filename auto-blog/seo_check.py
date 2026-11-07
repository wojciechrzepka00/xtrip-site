# SEO check for krakow-transfers.com — run from repo root: python3 auto-blog/seo_check.py
# Checks every public .html page: canonical points to itself, hreflang set is complete
# (self + x-default) and reciprocal, exactly one H1, title length, unique meta description
# of the right length, every JSON-LD block parses. Exit code 1 if anything fails.
import json, os, re, sys, html
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://krakow-transfers.com"
SKIP_DIRS = {"payments-backend", "auto-blog", "google-calendar-system", ".github", "node_modules", ".git", "images"}
SKIP_FILES = {"index-preview.html"}
TITLE_MIN, TITLE_MAX = 30, 65      # target ~50-60
DESC_MIN, DESC_MAX = 120, 160      # target 150-160

def pages():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith(".html") and f not in SKIP_FILES:
                fp = os.path.join(d, f)
                rel = os.path.relpath(fp, ROOT).replace(os.sep, "/")
                yield rel, fp

def url_of(rel):
    if rel == "index.html": return DOMAIN + "/"
    if rel.endswith("/index.html"): return DOMAIN + "/" + rel[:-len("index.html")]
    return DOMAIN + "/" + rel

def head_of(s):
    return s.split("</head>", 1)[0]

def attr(tag, name):
    m = re.search(r'\b' + name + r'\s*=\s*"([^"]*)"', tag)
    return html.unescape(m.group(1)) if m else None

def main():
    errors = defaultdict(list)
    info, descs, url2rel = {}, defaultdict(list), {}
    for rel, fp in sorted(pages()):
        s = open(fp, encoding="utf-8").read()
        h = head_of(s)
        u = url_of(rel); url2rel[u] = rel
        body = s.split("</head>", 1)[-1]
        # strip scripts so JS strings with "<h1" don't count
        body_ns = re.sub(r"<script\b.*?</script>", "", body, flags=re.S)
        canon = [attr(t, "href") for t in re.findall(r"<link[^>]*rel=\"canonical\"[^>]*>", h)]
        if len(canon) != 1: errors[rel].append(f"canonical count={len(canon)}")
        elif canon[0] != u: errors[rel].append(f"canonical not self: {canon[0]}")
        if re.search(r'<meta[^>]*name="robots"[^>]*noindex', s, re.I): errors[rel].append("noindex")
        alts = {}
        for t in re.findall(r"<link[^>]*hreflang=[^>]*>", h):
            alts[attr(t, "hreflang")] = attr(t, "href")
        info[rel] = alts
        h1 = len(re.findall(r"<h1[\s>]", body_ns, re.I))
        if h1 != 1: errors[rel].append(f"h1 count={h1}")
        tm = re.findall(r"<title>(.*?)</title>", h, re.S)
        if len(tm) != 1: errors[rel].append(f"title count={len(tm)}")
        else:
            t = html.unescape(tm[0]).strip()
            if not (TITLE_MIN <= len(t) <= TITLE_MAX): errors[rel].append(f"title len {len(t)}: {t}")
        dm = [attr(t, "content") for t in re.findall(r'<meta[^>]*name="description"[^>]*>', h)]
        if len(dm) != 1: errors[rel].append(f"description count={len(dm)}")
        else:
            d = dm[0].strip()
            descs[d].append(rel)
            if not (DESC_MIN <= len(d) <= DESC_MAX): errors[rel].append(f"description len {len(d)}")
        for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try: json.loads(blk)
            except Exception as e: errors[rel].append(f"JSON-LD parse error: {e}")
    for d, rels in descs.items():
        if len(rels) > 1:
            for r in rels: errors[r].append(f"duplicate description with {len(rels)-1} other page(s)")
    # hreflang: self + x-default + every target exists and carries the identical set
    for rel, alts in info.items():
        if not alts: continue
        u = url_of(rel)
        if u not in alts.values(): errors[rel].append("hreflang missing self")
        if "x-default" not in alts: errors[rel].append("hreflang missing x-default")
        for lang, href in alts.items():
            if not href.startswith(DOMAIN + "/"): errors[rel].append(f"hreflang other domain: {href}"); continue
            tr = url2rel.get(href)
            if not tr: errors[rel].append(f"hreflang target missing: {href}"); continue
            if info.get(tr) != alts: errors[rel].append(f"hreflang not reciprocal with {tr}")
    n = len(info)
    bad = {k: v for k, v in errors.items() if v}
    for rel in sorted(bad):
        for e in bad[rel]: print(f"FAIL {rel}: {e}")
    with_alts = sum(1 for a in info.values() if a)
    print(f"\nPages checked: {n} (with hreflang: {with_alts}); pages failing: {len(bad)}")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()

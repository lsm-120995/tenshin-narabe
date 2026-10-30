"""web/index.html から、GitHub Pages に置く docs/ フォルダを作る。

  .venv\\Scripts\\python build_pages.py

index.html に HTML の骨組みとホーム画面用の設定を足し、アイコンを描き出す。
"""
import io
import json
import os
import pathlib
import shutil

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "docs"
NAME = "点心ならべ"
THEME = "#17443d"
VERSION = 1  # 公開し直すたびに上げると、古いキャッシュが消える

HEAD = f"""<!doctype html>
<html lang="ja">
<head>
<meta name="description" content="蒸籠に隠れた点心を列ごとにそろえるパズル。">
<meta name="theme-color" content="{THEME}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{NAME}">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
<style>:root {{ padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }}</style>
"""

REGISTER = """<script>
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
</script>
"""

# 通信できるときは最新を取り、できないときは保存しておいた分で遊ぶ
SERVICE_WORKER = """const CACHE = "tenshin-v%d";
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return res;
      })
      .catch(() => caches.match(e.request).then(hit => hit || caches.match("index.html")))
  );
});
""" % VERSION

MANIFEST = {
    "name": NAME,
    "short_name": NAME,
    "lang": "ja",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": THEME,
    "theme_color": THEME,
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}

# 背景いっぱいに蒸籠と小籠包。端が切られても絵が残るよう、中央に寄せて描く
ICON = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{{size}}" height="{{size}}" viewBox="0 0 48 48">
  <rect width="48" height="48" fill="{THEME}"/>
  <g transform="translate(9.6 9.6) scale(.6)">
    <circle cx="24" cy="24" r="23" fill="#b9853f" stroke="#6e4619" stroke-width="1.5"/>
    <circle cx="24" cy="24" r="18.5" fill="#f5e6c5" stroke="#8a5e28"/>
    <path d="M12 31C10 22 18 16 24 12c6 4 14 10 12 19-5 5-19 5-24 0Z" fill="#fffaf0" stroke="#6e5a3a" stroke-width="1.3"/>
    <path d="M24 13 16 32M24 13l-3 21M24 13l3 21M24 13l8 19" fill="none" stroke="#c4ae85" stroke-width="1.2"/>
    <circle cx="24" cy="13" r="2.2" fill="#fffaf0" stroke="#6e5a3a"/>
  </g>
</svg>"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    page = page.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    # charset と viewport は HTML の先頭 1024 バイト以内に置く
    meta, sep, rest = page.partition("<title>")
    html = "<!doctype html>\n<html lang=\"ja\">\n<head>\n" + meta + HEAD.split("<head>\n", 1)[1] + sep + rest
    head_end = html.index("</style>\n\n<svg")
    html = html[:head_end] + "</style>\n</head>\n<body>\n" + html[head_end + len("</style>\n\n"):]
    html += REGISTER + "</body>\n</html>\n"
    (OUT / "index.html").write_text(html, encoding="utf-8")

    (OUT / "sw.js").write_text(SERVICE_WORKER, encoding="utf-8")
    (OUT / "manifest.webmanifest").write_text(
        json.dumps(MANIFEST, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    pygame.init()
    for size in (180, 192, 512):
        svg = ICON.format(size=size).encode("utf-8")
        image = pygame.image.load(io.BytesIO(svg), "icon.svg")
        assert image.get_size() == (size, size)
        pygame.image.save(image, str(OUT / f"icon-{size}.png"))


if __name__ == "__main__":
    build()
    print("built", sorted(p.name for p in OUT.iterdir()))

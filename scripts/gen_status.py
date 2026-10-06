"""Generate assets/status.svg: the name is typed once and stays, then the
status lines are typed out together and loop.

Edit LINES / timings below, then run: python scripts/gen_status.py
"""
import base64
import os
import re
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

NAME, NAME_COLOR, NAME_SIZE, NAME_TYPE = "Hi ~ I'm Tlrince", "#2F81F7", 22, 2.0  # typed once, seconds
LINES = ["Job hunting all in, but never skip the gym"]
COLOR = "#F78166"
FONT, WEIGHT, SIZE = "Fira Code", 700, 18
WIDTH, NAME_GAP, LINE_GAP, PAD = 480, 48, 38, 22  # px: name->first line, between lines, top/bottom
TYPE, HOLD, ERASE, BLANK = 4.0, 30.0, 1.0, 0.5  # seconds, status line loop

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "status.svg")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130 Safari/537.36"


def font_data_uri(text):
    """Subset the Google Font to just the characters we use and inline it as woff2."""
    q = urllib.parse.urlencode({"family": f"{FONT}:wght@{WEIGHT}", "text": "".join(sorted(set(text)))})
    css = urllib.request.urlopen(urllib.request.Request(f"https://fonts.googleapis.com/css2?{q}", headers={"User-Agent": UA})).read().decode()
    url = re.search(r"url\((https://[^)]+)\)", css).group(1)
    font = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA})).read()
    return "data:font/woff2;base64," + base64.b64encode(font).decode()


def name_animation(n, full):
    """Type the name once and keep it."""
    key_times = ";".join(f"{k / n:.4f}" for k in range(n + 1))
    vals = ";".join(f"{full * k / n:.1f}" for k in range(n + 1))
    return f'<animate attributeName="width" dur="{NAME_TYPE}s" fill="freeze" calcMode="discrete" keyTimes="{key_times}" values="{vals}"/>'


def width_animation(n, full):
    """Discrete clip-width steps: type n chars, hold, erase n chars, stay blank; starts after the name."""
    total = TYPE + HOLD + ERASE + BLANK
    times, values = [], []
    for k in range(n + 1):
        times.append(TYPE * k / n); values.append(full * k / n)
    for k in range(n, -1, -1):
        times.append(TYPE + HOLD + ERASE * (n - k) / n); values.append(full * k / n)
    times.append(total); values.append(0)
    key_times = ";".join(f"{t / total:.4f}" for t in times)
    vals = ";".join(f"{v:.1f}" for v in values)
    return f'<animate attributeName="width" begin="{NAME_TYPE}s" dur="{total}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{key_times}" values="{vals}"/>'


def main():
    # Fira Code advance width is 600/1000 em
    height = PAD * 2 + NAME_GAP + LINE_GAP * (len(LINES) - 1)
    nw = len(NAME) * NAME_SIZE * 0.6
    nx, ny = (WIDTH - nw) / 2, PAD
    body = [
        f'  <clipPath id="cn"><rect x="{nx:.1f}" y="{ny - NAME_SIZE:.1f}" width="0" height="{NAME_SIZE * 2}">{name_animation(len(NAME), nw)}</rect></clipPath>\n'
        f'  <text class="name" x="{nx:.1f}" y="{ny:.1f}" clip-path="url(#cn)">{escape(NAME)}</text>'
    ]
    for i, line in enumerate(LINES):
        w = len(line) * SIZE * 0.6
        x, y = (WIDTH - w) / 2, PAD + NAME_GAP + LINE_GAP * i
        body.append(
            f'  <clipPath id="c{i}"><rect x="{x:.1f}" y="{y - SIZE:.1f}" width="0" height="{SIZE * 2}">{width_animation(len(line), w)}</rect></clipPath>\n'
            f'  <text x="{x:.1f}" y="{y:.1f}" clip-path="url(#c{i})">{escape(line)}</text>'
        )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">
  <style>
    @font-face {{ font-family: 'status'; font-weight: {WEIGHT}; src: url({font_data_uri(NAME + "".join(LINES))}) format('woff2'); }}
    text {{ font: {WEIGHT} {SIZE}px 'status', monospace; fill: {COLOR}; dominant-baseline: central; white-space: pre; }}
    .name {{ font-size: {NAME_SIZE}px; fill: {NAME_COLOR}; }}
  </style>
{chr(10).join(body)}
</svg>
"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()

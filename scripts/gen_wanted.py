"""Generate a One Piece style WANTED poster whose bounty grows with GitHub activity.

bounty = profile views (Moe-Counter) * PER_VIEW
       + total stars                 * PER_STAR
       + all-time commits            * PER_COMMIT

Usage: GITHUB_TOKEN=xxx python scripts/gen_wanted.py [username]
"""
import datetime
import json
import os
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_USER", "tlrince")
ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "wanted.svg")
CACHE = os.path.join(ROOT, "assets", "stats.json")

PER_VIEW = 500_000
PER_STAR = 10_000_000
PER_COMMIT = 1_000_000

def graphql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}"},
    )
    return json.load(urllib.request.urlopen(req))["data"]["user"]


def fetch_github(user):
    data = graphql(
        """query($login: String!) {
          user(login: $login) {
            createdAt
            repositories(ownerAffiliations: OWNER, isFork: false, first: 100) { nodes { stargazerCount } }
          }
        }""",
        {"login": user},
    )
    stars = sum(r["stargazerCount"] for r in data["repositories"]["nodes"])

    # contributionsCollection spans at most one year, so sum commits year by year
    first, last = int(data["createdAt"][:4]), datetime.date.today().year
    fields = "\n".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
        "{ totalCommitContributions restrictedContributionsCount }"
        for y in range(first, last + 1)
    )
    years = graphql(f"query($login: String!) {{ user(login: $login) {{ {fields} }} }}", {"login": user})
    commits = sum(v["totalCommitContributions"] for v in years.values())
    return stars, commits


def fetch_views(user):
    """Read-only total from Moe-Counter (does not bump the counter). None on failure."""
    req = urllib.request.Request(
        f"https://count.getloli.com/api/stats/series/{user}",
        headers={"User-Agent": "Mozilla/5.0 (profile-bounty)", "Accept": "application/json"},
    )
    try:
        return int(json.load(urllib.request.urlopen(req, timeout=20))["total"])
    except Exception as e:  # Cloudflare challenge, timeout, ...
        print(f"views fetch failed ({e}), keeping last known value")
        return None


def load_cache():
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def fetch_stats(user):
    stars, commits = fetch_github(user)
    views = fetch_views(user)
    if views is None:
        views = load_cache().get("views", 0)
    return {"views": views, "stars": stars, "commits": commits}


def bounty(s):
    return s["views"] * PER_VIEW + s["stars"] * PER_STAR + s["commits"] * PER_COMMIT


def render(name, amount, s):
    amount_text = f"{amount:,}-"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="260" height="380" viewBox="0 0 260 380">
  <style>
    .poster {{ transform-origin: 130px 0; animation: sway 6s ease-in-out infinite; }}
    @keyframes sway {{ 0%,100% {{ transform: rotate(-1.2deg); }} 50% {{ transform: rotate(1.2deg); }} }}
    .serif {{ font-family: 'Times New Roman', Georgia, 'Songti SC', serif; fill: #3a2614; }}
  </style>
  <defs>
    <radialGradient id="paper" cx="50%" cy="45%" r="75%">
      <stop offset="0%" stop-color="#f6e7c4"/>
      <stop offset="70%" stop-color="#e8d09c"/>
      <stop offset="100%" stop-color="#c9a466"/>
    </radialGradient>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#7fb6d9"/>
      <stop offset="65%" stop-color="#cfe6f1"/>
      <stop offset="65%" stop-color="#2f6f9f"/>
      <stop offset="100%" stop-color="#1d4e78"/>
    </linearGradient>
  </defs>
  <g class="poster">
    <rect x="8" y="10" width="244" height="360" rx="3" fill="url(#paper)" stroke="#8a6534" stroke-width="2"/>
    <circle cx="130" cy="16" r="3.5" fill="#6b4a22"/>

    <text x="130" y="68" text-anchor="middle" class="serif" font-size="46" font-weight="900" letter-spacing="3">WANTED</text>

    <!-- photo -->
    <rect x="30" y="82" width="200" height="150" fill="url(#sky)" stroke="#3a2614" stroke-width="3"/>
    <g transform="translate(130 160)">
      <!-- crossbones -->
      <g stroke="#f4f1ea" stroke-width="9" stroke-linecap="round">
        <line x1="-44" y1="-6" x2="44" y2="46"/>
        <line x1="44" y1="-6" x2="-44" y2="46"/>
      </g>
      <g fill="#f4f1ea">
        <circle cx="-48" cy="-10" r="6"/><circle cx="-50" cy="-1" r="6"/>
        <circle cx="48" cy="-10" r="6"/><circle cx="50" cy="-1" r="6"/>
        <circle cx="-48" cy="42" r="6"/><circle cx="-50" cy="51" r="6"/>
        <circle cx="48" cy="42" r="6"/><circle cx="50" cy="51" r="6"/>
        <!-- skull -->
        <ellipse cx="0" cy="8" rx="30" ry="28"/>
        <rect x="-15" y="26" width="30" height="16" rx="5"/>
      </g>
      <g fill="#1d1d1d">
        <ellipse cx="-11" cy="10" rx="8" ry="9"/>
        <ellipse cx="11" cy="10" rx="8" ry="9"/>
        <path d="M0 20 l-4 8 h8 z"/>
        <rect x="-8" y="33" width="2.5" height="8"/><rect x="-1.25" y="33" width="2.5" height="8"/><rect x="5.5" y="33" width="2.5" height="8"/>
      </g>
      <!-- straw hat -->
      <ellipse cx="0" cy="-12" rx="50" ry="11" fill="#f0c94a" stroke="#a67c1a" stroke-width="2"/>
      <path d="M-26 -14 Q-26 -46 0 -46 Q26 -46 26 -14 Z" fill="#f0c94a" stroke="#a67c1a" stroke-width="2"/>
      <path d="M-26 -20 Q0 -14 26 -20 L26 -14 Q0 -8 -26 -14 Z" fill="#c8312b"/>
    </g>

    <text x="130" y="262" text-anchor="middle" class="serif" font-size="22" font-weight="700" letter-spacing="2">DEAD OR ALIVE</text>
    <text x="130" y="298" text-anchor="middle" class="serif" font-size="30" font-weight="900" letter-spacing="2">{name.upper()}</text>
    <text x="34" y="334" class="serif" font-size="24" font-weight="900">฿</text>
    <text x="226" y="334" text-anchor="end" class="serif" font-size="23" font-weight="900" letter-spacing="1">{amount_text}</text>
    <text x="130" y="356" text-anchor="middle" class="serif" font-size="9" opacity="0.75">{s["views"]} views · {s["stars"]} stars · {s["commits"]} commits</text>
    <text x="244" y="364" text-anchor="end" class="serif" font-size="8" font-weight="700" opacity="0.6">MARINE</text>
  </g>
</svg>
"""


def main():
    stats = fetch_stats(USER)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(USER, bounty(stats), stats))
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"{USER}: {stats} -> ฿{bounty(stats):,}")


if __name__ == "__main__":
    main()

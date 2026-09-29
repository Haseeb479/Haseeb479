#!/usr/bin/env python3
import json, os, urllib.request, urllib.error
from datetime import datetime, timezone

LOGIN = os.environ.get("GH_LOGIN", "Haseeb479")
TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    raise SystemExit("GITHUB_TOKEN is required")

QUERY = """
query($login:String!) {
  user(login:$login) {
    name
    login
    followers { totalCount }
    following { totalCount }
    repositories(first:100, ownerAffiliations:OWNER, privacy:PUBLIC) {
      totalCount
      nodes {
        name
        stargazerCount
        forkCount
        languages(first:10, orderBy:{field:SIZE, direction:DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { contributionCount date }
        }
      }
    }
  }
}
"""

def graphql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": LOGIN
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]

def esc(s):
    return (str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            .replace('"',"&quot;"))

def svg_header(w,h,title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">
<rect width="{w}" height="{h}" fill="#fff"/>
<g font-family="JetBrains Mono,monospace" fill="#111">
<text x="25" y="38" font-size="13">{esc(title)}</text>'''

def write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

u = graphql(QUERY, {"login": LOGIN})
repos = u["repositories"]["nodes"]
calendar = u["contributionsCollection"]["contributionCalendar"]
days = [d for w in calendar["weeks"] for d in w["contributionDays"]]
total = calendar["totalContributions"]

stars = sum(r["stargazerCount"] for r in repos)
forks = sum(r["forkCount"] for r in repos)

langs = {}
for r in repos:
    for e in r["languages"]["edges"]:
        langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
top_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:8]
lang_total = sum(v for _,v in top_langs) or 1

today = datetime.now(timezone.utc).date()
recent = days[-365:] if len(days) > 365 else days
active = sum(1 for d in recent if d["contributionCount"] > 0)

# Find current streak and best streak from contribution days.
best = cur = 0
for d in days:
    if d["contributionCount"] > 0:
        cur += 1
        best = max(best, cur)
    else:
        cur = 0
cur = 0
for d in reversed(days):
    if d["contributionCount"] > 0:
        cur += 1
    else:
        break

write("stats.svg", svg_header(1200,220,"GITHUB / OVERVIEW") + f'''
<text x="25" y="88" font-size="32" font-weight="700">{total:,}</text>
<text x="25" y="112" font-size="12" fill="#666">contributions in the current GitHub contribution calendar</text>
<text x="360" y="88" font-size="32" font-weight="700">{len(repos)}</text>
<text x="360" y="112" font-size="12" fill="#666">public repositories</text>
<text x="650" y="88" font-size="32" font-weight="700">{stars:,}</text>
<text x="650" y="112" font-size="12" fill="#666">repository stars</text>
<text x="880" y="88" font-size="32" font-weight="700">{forks:,}</text>
<text x="880" y="112" font-size="12" fill="#666">forks</text>
<path d="M25 170H1175" stroke="#111" stroke-width="2"/>
<text x="25" y="195" font-size="12" fill="#666">FOLLOWERS {u["followers"]["totalCount"]} · FOLLOWING {u["following"]["totalCount"]} · UPDATED {today.isoformat()}</text>
</g></svg>''')

write("streak.svg", svg_header(580,190,"CONTRIBUTION STREAK") + f'''
<text x="25" y="88" font-size="34" font-weight="700">{cur} DAYS</text>
<text x="25" y="120" font-size="13" fill="#666">current streak</text>
<text x="300" y="88" font-size="34" font-weight="700">{best} DAYS</text>
<text x="300" y="120" font-size="13" fill="#666">best streak</text>
<path d="M25 150H555" stroke="#111" stroke-width="2"/>
<text x="25" y="172" font-size="11" fill="#666">last 365 days: {active} active days</text>
</g></svg>''')

rows = []
for i,(name,size) in enumerate(top_langs):
    pct = size / lang_total * 100
    y = 65 + i*15
    rows.append(f'<text x="25" y="{y}" font-size="11">{esc(name)}</text><text x="480" y="{y}" text-anchor="end" font-size="11">{pct:.1f}%</text>')
write("langs.svg", svg_header(580,190,"TOP LANGUAGES") + "\n".join(rows) + '''
<path d="M25 175H555" stroke="#111" stroke-width="2"/>
</g></svg>''')

# Compact 52-week contribution heatmap.
weeks = calendar["weeks"][-52:]
rects = []
for x,w in enumerate(weeks):
    for y,d in enumerate(w["contributionDays"]):
        count=d["contributionCount"]
        opacity=0.10 if count==0 else min(0.20 + count/8*0.75, 0.95)
        rects.append(f'<rect x="{25+x*21}" y="{62+y*19}" width="14" height="14" rx="2" fill="#111" fill-opacity="{opacity:.2f}"/>')
write("year.svg", svg_header(1200,240,"LAST 52 WEEKS") + "".join(rects) + f'''
<text x="25" y="220" font-size="11" fill="#666">{total:,} total contributions · darker cells represent more activity</text>
</g></svg>''')

print(f"Updated GitHub profile stats for {LOGIN}: {total} contributions, {len(repos)} public repos")

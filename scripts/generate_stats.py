#!/usr/bin/env python3
"""Generate Haseeb479's GitHub profile graphics from GitHub GraphQL.
Standard library only. No third-party stats service."""
import json, os, urllib.request
from datetime import datetime, timezone

LOGIN=os.getenv("GH_LOGIN","Haseeb479")
TOKEN=os.getenv("GITHUB_TOKEN")
if not TOKEN: raise SystemExit("GITHUB_TOKEN is required")

QUERY="""query($login:String!){
 user(login:$login){
  contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}
  repositories(first:100,ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false){
   nodes{stargazerCount forkCount languages(first:12,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}
  }
 }
}"""

def api():
 body=json.dumps({"query":QUERY,"variables":{"login":LOGIN}}).encode()
 req=urllib.request.Request("https://api.github.com/graphql",data=body,headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json","User-Agent":LOGIN})
 with urllib.request.urlopen(req,timeout=30) as r: data=json.load(r)
 if data.get("errors"): raise SystemExit(str(data["errors"]))
 return data["data"]["user"]

def esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def frame(w,h):
 return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none">
<style>.t{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}}.d{{fill:#6e7681}}.e{{fill:#424a53}}.r{{stroke:#d8dee4}}.w{{fill:#6e7681;opacity:.13}}
@media(prefers-color-scheme:dark){{.d{{fill:#c9d1d9}}.e{{fill:#f0f6fc}}.r{{stroke:#30363d}}.w{{fill:#c9d1d9;opacity:.16}}}}</style>'''

def streak(days):
 best=cur=0; run=0
 for d in days:
  if d["contributionCount"]>0: run+=1; best=max(best,run)
  else: run=0
 for d in reversed(days):
  if d["contributionCount"]>0: cur+=1
  else: break
 return cur,best

u=api()
cal=u["contributionsCollection"]["contributionCalendar"]
days=[d for w in cal["weeks"] for d in w["contributionDays"]]
weekly=[sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]]
repos=u["repositories"]["nodes"]
stars=sum(r["stargazerCount"] for r in repos); forks=sum(r["forkCount"] for r in repos)
langs={}
for r in repos:
 for e in (r.get("languages") or {}).get("edges",[]):
  langs[e["node"]["name"]]=langs.get(e["node"]["name"],0)+e["size"]
top=sorted(langs.items(),key=lambda x:(-x[1],x[0]))[:5]
total_bytes=sum(v for _,v in top) or 1
cur,best=streak(days)

# Hero + animated weekly sparkline + progress metrics.
mx=max(weekly) or 1
active_days=sum(1 for d in days if d["contributionCount"]>0)
calendar_days=len(days) or 365
active_pct=(active_days/calendar_days)*100
year_pct=min(100,(active_days/calendar_days)*100)

pts=[]
for i,v in enumerate(weekly):
 x=i*620/max(len(weekly)-1,1); y=94-(v/mx)*42; pts.append((x,y))
path="M"+" ".join(f"{'L' if i else ''}{x:.1f},{y:.1f}" for i,(x,y) in enumerate(pts))

def bar(x,y,width,pct,height=6):
 fill=max(0,min(width,width*pct/100))
 return f'<path d="M{x} {y}H{x+width}" class="r"/><rect x="{x}" y="{y-height+1}" width="{fill:.1f}" height="{height}" rx="2" class="b"/>'

stats=frame(620,190)+f'''<style>.b{{fill:#6e7681}}@media(prefers-color-scheme:dark){{.b{{fill:#f0f6fc}}}}</style>
<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin=".1s" dur=".45s" fill="freeze"/>
<text x="0" y="39" class="e t" font-size="40" font-weight="600">{cal["totalContributions"]:,}</text>
<text x="0" y="57" class="d t" font-size="10">CONTRIBUTIONS · LAST YEAR</text>
<text x="215" y="39" class="e t" font-size="24" font-weight="600">{active_days}</text>
<text x="215" y="57" class="d t" font-size="10">ACTIVE DAYS</text>
<text x="350" y="39" class="e t" font-size="24" font-weight="600">{cur}</text>
<text x="350" y="57" class="d t" font-size="10">CURRENT STREAK</text>
<text x="480" y="39" class="e t" font-size="24" font-weight="600">{best}</text>
<text x="480" y="57" class="d t" font-size="10">LONGEST STREAK</text></g>

<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin=".25s" dur=".45s" fill="freeze"/>
<text x="0" y="76" class="d t" font-size="9">ACTIVE DAYS / {calendar_days} DAYS</text>
{bar(0,87,180,active_pct)}
<text x="195" y="76" class="d t" font-size="9">{active_pct:.0f}%</text>
<text x="270" y="76" class="d t" font-size="9">CURRENT STREAK / LONGEST</text>
{bar(270,87,180,(cur/best*100 if best else 0))}
<text x="465" y="76" class="d t" font-size="9">{cur}/{best}</text>
<text x="500" y="76" class="d t" font-size="9">YEAR ACTIVITY</text>
{bar(500,87,120,year_pct)}</g>

<path d="M0 105H620" class="r"/>
<path d="{path} L620 105 L0 105Z" class="w"/>
<path d="{path}" stroke="#6e7681" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="0 900"><animate attributeName="stroke-dasharray" from="0 900" to="900 0" begin=".5s" dur="1.3s" fill="freeze"/></path>
<text x="0" y="126" class="d t" font-size="9">WEEKLY ACTIVITY · {len(weekly)} WEEKS</text>
<text x="0" y="146" class="d t" font-size="9">PUBLIC REPOSITORIES · {len(repos)}   STARS · {stars}   FORKS · {forks}</text>
<text x="0" y="166" class="d t" font-size="9">GITHUB GRAPHQL · UPDATED {datetime.now(timezone.utc).date().isoformat()}</text>
</svg>'''
open("stats.svg","w",encoding="utf8").write(stats)

# Dedicated streak panel with active-day and streak progress highlights.
st=frame(620,142)+f'''<style>.b{{fill:#6e7681}}@media(prefers-color-scheme:dark){{.b{{fill:#f0f6fc}}}}</style>
<line x1="310" y1="12" x2="310" y2="130" class="r"/>
<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin=".15s" dur=".4s" fill="freeze"/>
<text x="34" y="25" class="d t" font-size="10">CURRENT STREAK</text>
<text x="34" y="58" class="e t" font-size="32" font-weight="600">{cur}</text><text x="72" y="58" class="d t" font-size="11">days</text>
<text x="34" y="76" class="d t" font-size="9">progress vs longest streak</text>
{bar(34,88,235,(cur/best*100 if best else 0))}
<text x="34" y="105" class="d t" font-size="9">{(cur/best*100 if best else 0):.0f}% of longest</text></g>
<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin=".3s" dur=".4s" fill="freeze"/>
<text x="344" y="25" class="d t" font-size="10">LONGEST STREAK</text>
<text x="344" y="58" class="e t" font-size="32" font-weight="600">{best}</text><text x="382" y="58" class="d t" font-size="11">days</text>
<text x="344" y="76" class="d t" font-size="9">active days this year</text>
{bar(344,88,235,active_pct)}
<text x="344" y="105" class="d t" font-size="9">{active_days}/{calendar_days} active days · {active_pct:.0f}%</text></g>
<text x="34" y="130" class="d t" font-size="9">REAL GITHUB CONTRIBUTION DATA · NO SYNTHETIC ACTIVITY</text></svg>'''
open("streak.svg","w",encoding="utf8").write(st)

ls=frame(620,150)+'<text x="34" y="15" class="d t" font-size="9" letter-spacing="1.2">TOP LANGUAGES / PUBLIC REPOSITORIES</text>'
maxv=max([v for _,v in top],default=1)
for i,(name,val) in enumerate(top):
 y=43+i*22; width=435*val/maxv; pct=val/total_bytes*100
 ls+=f'<text x="34" y="{y}" class="e t" font-size="11">{esc(name.lower())}</text><path d="M135 {y-5}H570" class="r"/><rect x="135" y="{y-8}" width="{width:.1f}" height="7" rx="2" fill="#6e7681"><animate attributeName="width" from="0" to="{width:.1f}" begin="{.25+i*.08:.2f}s" dur=".7s" fill="freeze"/></rect><text x="590" y="{y}" class="d t" font-size="10" text-anchor="end">{pct:.0f}%</text>'
ls+='</svg>'
open("langs.svg","w",encoding="utf8").write(ls)

# Character heatmap using the reference-style : + # @ ramp.
ramp=[" ", " :", " +"," #"," @"]
year=frame(620,170)+'<text x="34" y="16" class="d t" font-size="9" letter-spacing="1.2">THE YEAR / CONTRIBUTION MAP</text><text x="34" y="35" class="d t" font-size="10">less</text><text x="540" y="35" class="d t" font-size="10" text-anchor="end">more</text>'
weeks=cal["weeks"][-53:]
for row in range(7):
 s=""
 for w in weeks:
  ds=w["contributionDays"]
  d=ds[row] if row<len(ds) else {"contributionCount":0}
  n=d["contributionCount"]
  s+=" " if n==0 else ":" if n<=2 else "+" if n<=5 else "#" if n<=9 else "@"
 year+=f'<text x="34" y="{62+row*12}" class="e t" font-size="10" xml:space="preserve">{s}</text>'
year+='<text x="34" y="158" class="d t" font-size="9">generated from GitHub contribution calendar · character ramp: : + # @</text></svg>'
open("year.svg","w",encoding="utf8").write(year)
print(f"Generated profile graphics for {LOGIN}: {cal['totalContributions']} contributions, {active_days} active days, current streak {cur}, longest streak {best}.")

#!/usr/bin/env python3
"""Gera um mapa SVG a partir de dados públicos reais; nunca inventa contribuições."""
import datetime as dt
import html
import json
import os
import pathlib
import re
import requests
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parents[1]
USERNAME = os.environ.get("GITHUB_PROFILE_USERNAME", "Matheuslinspg3")
PALETTE = ["#2B0C17", "#730019", "#C80F24", "#F25B19", "#FFB81D"]
MONTHS = ["JAN","FEV","MAR","ABR","MAI","JUN","JUL","AGO","SET","OUT","NOV","DEZ"]

def parse(source):
    soup = BeautifulSoup(source, "html.parser")
    tips = {el.get("for"): el.get_text(" ",strip=True) for el in soup.select("tool-tip[for]")}
    out = {}
    for el in soup.select("[data-date][data-level]"):
        iso = el.get("data-date","")
        try: dt.date.fromisoformat(iso)
        except ValueError: continue
        raw = el.get("data-level","")
        if not raw.isdigit(): continue
        level = min(4, int(raw))
        label = el.get("aria-label", "") or tips.get(el.get("id"), "") or el.get("title", "")
        count = el.get("data-count","")
        if str(count).isdigit():
            count = int(count)
        else:
            m = re.search(r"(?<!\w)(\d[\d,\.]*)\s+contributions?\b",label,re.I)
            count = int(re.sub(r"[^\d]","",m.group(1))) if m else (0 if level == 0 else None)
        if count is None:
            raise RuntimeError("Data de contribuição ativa sem quantidade: "+iso)
        out[iso]={"date":iso,"count":count,"level":level}
    if len(out)<300:
        raise RuntimeError("HTML incompleto ou formato alterado: apenas %d datas" % len(out))
    return [out[k] for k in sorted(out)]

def text(x,y,t,color="#ECD6D7",size=13,extra=""):
    return '<text x="%s" y="%s" fill="%s" font-size="%s" font-family="Arial,Helvetica,sans-serif" %s>%s</text>'%(x,y,color,size,extra,html.escape(str(t)))

def render(days):
    today=dt.date.today()
    first=today-dt.timedelta(days=(today.weekday()+1)%7+52*7)
    by={x["date"]:x for x in days}
    total=sum(x["count"] for x in days)
    active=sum(x["count"]>0 for x in days)
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="286" viewBox="0 0 1200 286" role="img" aria-label="Contribuições públicas reais de '+USERNAME+'">',
    '<defs><linearGradient id="border"><stop stop-color="#FFD647"/><stop offset=".45" stop-color="#FF6716"/><stop offset="1" stop-color="#A0002C"/></linearGradient><linearGradient id="bg"><stop stop-color="#24080E"/><stop offset="1" stop-color="#14040B"/></linearGradient></defs>',
    '<rect x="2" y="2" width="1196" height="282" rx="25" fill="url(#bg)" stroke="url(#border)" stroke-width="1.5"/>',
    text(30,46,"Contribuições no GitHub","#FFF5F1",24,'font-weight="800"'),
    text(1168,46,f"{total:,}".replace(",",".")+" contribuições no período","#FFBD5C",16,'text-anchor="end" font-weight="700"')]
    for w in range(53):
        base=first+dt.timedelta(weeks=w)
        if base.day<=7:
            out.append(text(125+w*17.5,78,MONTHS[base.month-1],"#D8A8B0",12))
        for d in range(7):
            day=base+dt.timedelta(days=d)
            if day>today: continue
            item=by.get(day.isoformat())
            lvl=min(4,max(0,int(item["level"]))) if item else 0
            out.append('<rect x="%s" y="%s" width="13.5" height="13.5" rx="3" fill="%s"/>'%(125+w*17.5,91+d*17.5,PALETTE[lvl]))
    for y,lab in [(128,"SEG"),(163,"QUA"),(198,"SEX")]:
        out.append(text(76,y,lab,"#E3C6C7",12))
    out.append('<path d="M30 235H1170" stroke="#60333A"/>')
    out.append(text(30,264,f"{active} dias com contribuições no período","#D8B1B7",13))
    out.append(text(971,263,"MENOS","#D8B1B7",11))
    for i,c in enumerate(PALETTE):
        out.append('<rect x="%d" y="248" width="16" height="16" rx="3" fill="%s"/>'%(1017+i*24,c))
    out.append(text(1168,263,"MAIS","#D8B1B7",11,'text-anchor="end"'))
    return "\n".join(out+["</svg>"])+"\n"

if __name__=="__main__":
    url="https://github.com/users/"+USERNAME+"/contributions"
    response=requests.get(url,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"en-US,en;q=0.9"},timeout=25)
    response.raise_for_status()
    days=parse(response.text)
    js={"username":USERNAME,"fetched_at":dt.datetime.now(dt.timezone.utc).isoformat(),"status":"ok","days":days}
    # Só altera os arquivos depois de validar toda a resposta.
    (ROOT/"data").mkdir(exist_ok=True)
    (ROOT/"assets").mkdir(exist_ok=True)
    (ROOT/"data/contributions.json").write_text(json.dumps(js,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"assets/contributions.svg").write_text(render(days),encoding="utf-8")
    print("Contribuições reais processadas:",len(days))

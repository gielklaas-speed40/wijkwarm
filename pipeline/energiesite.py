"""Pagina's per gemeente en wijk over energieverbruik, woningvoorraad en subsidie."""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import sys
from collections import defaultdict

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
from common import CSS, CONFIG, e, datum_nl, slugify  # noqa: E402

BASIS_URL = "https://wijkwarm.nl/"
VERGUNNINGEN_URL = "https://vergunningenradar.nl/"

with open(os.path.join(HIER, "subsidies.json"), encoding="utf-8") as f:
    SUBSIDIES = json.load(f)

MAATREGELEN = {
    "isolatie": "Isolatie", "warmtepomp": "Warmtepomp", "zonnepanelen": "Zonnepanelen", "thuisbatterij": "Thuisbatterij",
}

EXTRA_CSS = """
:root{--warm:#c2571a;--warm-soft:#fbe9dd;--acc-soft:#e3f2ee}
h1,h2,.hero h1,.kern b{font-family:Archivo,-apple-system,"Segoe UI",Roboto,sans-serif}
h1{font-size:34px;font-weight:800;letter-spacing:-.3px;line-height:1.1}
h2{font-size:19px;font-weight:700}
header .brand{font-family:Archivo,sans-serif;font-weight:800;font-size:20px;letter-spacing:-.2px}
header .brand span{color:var(--warm)}
.hero{padding:34px 0 8px;max-width:760px}
.hero p.lead{font-size:17px;margin-top:10px}
.zoek{position:relative;max-width:560px;margin:18px 0 6px}
.zoek input{width:100%;font:inherit;font-size:17px;padding:13px 16px;border:2px solid var(--ink);border-radius:8px;background:#fff}
.zoek input:focus{outline:none;border-color:var(--warm)}
.zoek ul{position:absolute;left:0;right:0;top:100%;margin:4px 0 0;padding:6px 0;list-style:none;background:#fff;border:1px solid var(--line);border-radius:8px;box-shadow:0 8px 24px rgba(21,32,43,.12);z-index:5;max-height:320px;overflow:auto}
.zoek ul:empty{display:none}
.zoek li a{display:block;padding:8px 14px;text-decoration:none;color:var(--ink)}
.zoek li a:hover,.zoek li.actief a{background:var(--acc-soft)}
.zoek li a span{color:var(--mut);font-size:13px;margin-left:6px}
.kern{display:flex;gap:28px 40px;flex-wrap:wrap;align-items:flex-end;margin:22px 0 6px}
.kern div{min-width:120px}
.kern b{display:block;font-size:38px;font-weight:800;line-height:1;color:var(--ink)}
.kern b.groot{font-size:56px;color:var(--warm)}
.kern span{display:block;color:var(--mut);font-size:13px;margin-top:6px;max-width:200px}
.staven{margin:14px 0 26px}
.staven .rij{display:grid;grid-template-columns:130px 1fr 90px;align-items:center;gap:12px;margin:0 0 8px;font-size:14px}
.staven .rij .lbl{color:var(--mut)}
.staven .rij.wijk .lbl{color:var(--ink);font-weight:600}
.staven .balk{height:14px;background:#e6eaef;border-radius:0 4px 4px 0;position:relative}
.staven .balk i{display:block;height:100%;border-radius:0 4px 4px 0;background:#9aa8b8}
.staven .rij.wijk .balk i{background:var(--warm)}
.staven.zon .rij.wijk .balk i{background:var(--acc)}
.staven .val{font-variant-numeric:tabular-nums;font-weight:600;text-align:right}
.staven .titel{font-weight:700;margin:0 0 8px}
.tweekolom{display:grid;grid-template-columns:1fr 1fr;gap:20px 40px}
@media (max-width:700px){.tweekolom{grid-template-columns:1fr}.staven .rij{grid-template-columns:96px 1fr 70px}h1{font-size:28px}.kern b.groot{font-size:44px}}
.cijfers td.num{width:110px}
.advies p{margin:0 0 10px;max-width:760px;font-size:16px}
.knoppen{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0 4px}
.knoppen a{display:inline-block;background:var(--acc);color:#fff;text-decoration:none;padding:9px 16px;border-radius:6px;font-weight:600}
.toplijst td.num{width:120px}
.reken{background:var(--panel);border:1px solid var(--line);padding:18px 20px;margin:12px 0 24px;max-width:720px}
.reken .velden{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px 20px;margin:4px 0 14px}
.reken label{display:block;font-size:13px;color:var(--mut);margin-bottom:4px}
.reken input,.reken select{width:100%;font:inherit;font-size:16px;padding:8px 10px;border:1px solid var(--line);border-radius:6px;background:#fff}
.reken .uit{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px 24px;border-top:1px solid var(--line);padding-top:14px}
.reken .uit b{display:block;font-family:Archivo,sans-serif;font-size:30px;font-weight:800;line-height:1.1;color:var(--acc)}
.reken .uit b.warm{color:var(--warm)}
.reken .uit span{display:block;font-size:13px;color:var(--mut);margin-top:4px}
.reken p.klein{margin:12px 0 0}
.maatregelen{display:flex;flex-wrap:wrap;gap:8px 18px;margin:6px 0 18px;font-size:15px}
.filter{margin:6px 0 12px;max-width:360px}
.filter input{width:100%;font:inherit;padding:9px 12px;border:1px solid var(--line);border-radius:6px}
"""

ZOEK_JS = r"""<script>
(function(){
var inp=document.getElementById('zoek');if(!inp)return;
var lijst=JSON.parse(document.getElementById('zoekdata').textContent);
var ul=document.getElementById('zoekres');var act=-1;
function norm(t){return t.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');}
function render(q){ul.innerHTML='';act=-1;q=norm(q.trim());if(q.length<2)return;
 var hits=[];for(var i=0;i<lijst.length&&hits.length<12;i++){var r=lijst[i];if(norm(r[0]).indexOf(q)===0||norm(r[0]).indexOf(' '+q)>=0||(r[1]&&norm(r[1]).indexOf(q)===0&&hits.length<6))hits.push(r);}
 if(!hits.length){for(var j=0;j<lijst.length&&hits.length<12;j++){var s=lijst[j];if(norm(s[0]).indexOf(q)>=0)hits.push(s);}}
 hits.forEach(function(r){var li=document.createElement('li');var a=document.createElement('a');a.href=r[2];a.textContent=r[0];if(r[1]){var sp=document.createElement('span');sp.textContent=r[1];a.appendChild(sp);}li.appendChild(a);ul.appendChild(li);});}
inp.addEventListener('input',function(){render(inp.value);});
inp.addEventListener('keydown',function(e){var items=ul.querySelectorAll('li');if(!items.length)return;
 if(e.key==='ArrowDown'){act=Math.min(act+1,items.length-1);}else if(e.key==='ArrowUp'){act=Math.max(act-1,0);}else if(e.key==='Enter'){e.preventDefault();var t=items[act>=0?act:0].querySelector('a');if(t)location.href=t.href;return;}else return;
 e.preventDefault();items.forEach(function(li,i){li.classList.toggle('actief',i===act);});});
document.addEventListener('click',function(e){if(!inp.parentNode.contains(e.target))ul.innerHTML='';});
})();
</script>"""

FILTER_JS = """<script>
(function(){var f=document.getElementById('filter');if(!f)return;var rijen=document.querySelectorAll('table.wijken tbody tr');
f.addEventListener('input',function(){var q=f.value.toLowerCase();rijen.forEach(function(r){r.style.display=r.textContent.toLowerCase().indexOf(q)>=0?'':'none';});});})();
</script>"""


def staven(titel: str, rijen: list[tuple[str, float | None, bool]], eenheid: str, klasse: str = "") -> str:
    """Horizontale staafjes: [(label, waarde, is_wijk)], breedte relatief aan het maximum."""
    waarden = [w for _, w, _ in rijen if w is not None]
    if not waarden:
        return ""
    mx = max(waarden) or 1
    uit = [f'<div class="staven {klasse}"><p class="titel">{e(titel)}</p>']
    for label, w, is_wijk in rijen:
        if w is None:
            continue
        pct = max(2, round(w / mx * 100))
        uit.append(f'<div class="rij{" wijk" if is_wijk else ""}"><span class="lbl">{e(label)}</span><div class="balk"><i style="width:{pct}%"></i></div><span class="val">{getal(w, eenheid)}</span></div>')
    uit.append("</div>")
    return "".join(uit)


def getal(w, eenheid: str = "", decimalen: int = 0) -> str:
    if w is None or w == "":
        return "onbekend"
    try:
        w = float(w)
    except (TypeError, ValueError):
        return e(w)
    s = f"{w:,.{decimalen}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s}{eenheid}"


BRONTEKST = "CBS Kerncijfers wijken en buurten"


def brontekst(bronnen: dict | None) -> str:
    if not bronnen or not bronnen.get("kerncijfers"):
        return "CBS Kerncijfers wijken en buurten."
    k = bronnen["kerncijfers"]
    delen = [f"woningcijfers uit CBS Kerncijfers wijken en buurten {k.get('jaar', '')}"]
    if bronnen.get("energie"):
        delen.append(f"gas en stroom uit CBS Energieverbruik particuliere woningen {bronnen['energie'].get('jaar', '')} (verbruik over {int(bronnen['energie'].get('jaar', 0) or 0) - 1})")
    if bronnen.get("aanvulling"):
        delen.append(f"zonnestroom en aardgasvrij uit de kerncijfers {bronnen['aanvulling'].get('jaar', '')}")
    return "Bron: " + ", ".join(delen) + "."


def pagina(titel: str, body: str, diepte: int, omschrijving: str, canonical: str) -> str:
    root = "../" * diepte
    adsense = ""
    if CONFIG.get("adsense_client"):
        adsense = f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={e(CONFIG["adsense_client"])}" crossorigin="anonymous"></script>'
    return f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titel)}</title>
<meta name="description" content="{e(omschrijving)}">
<link rel="canonical" href="{BASIS_URL}{canonical}">
{adsense}
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&display=swap">
<style>{CSS}{EXTRA_CSS}</style>
</head>
<body>
<header><div class="wrap">
<a class="brand" href="{root}">Wijk<span>warm</span></a>
<nav><a href="{root}">Gemeenten</a><a href="{root}subsidie.html">Subsidie {SUBSIDIES['jaar']}</a><a href="{root}over.html">Over de data</a><a href="{VERGUNNINGEN_URL}">Vergunningen</a></nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">{BRONTEKST} Subsidiebedragen van RVO, controleer altijd de actuele regeling. Een dienst van <a href="https://klaasystems.nl/">Klaasystems</a>.</div></footer>
</body>
</html>
"""


def vergelijk(w: dict, g: dict, nl: dict, veld: str, eenheid: str = "") -> str:
    return f"<tr><td>{{label}}</td><td class=\"num\">{getal(w.get(veld), eenheid)}</td><td class=\"num\">{getal(g.get(veld), eenheid)}</td><td class=\"num\">{getal(nl.get(veld), eenheid)}</td></tr>"


def cijfertabel(w: dict, g: dict, nl: dict, wijknaam: str, gemeentenaam: str) -> str:
    rijen = [
        ("Woningen", "woningen", ""),
        ("Koopwoningen", "koop_pct", "%"),
        ("In bezit woningcorporatie", "corporatie_pct", "%"),
        ("Eengezinswoningen", "eengezins_pct", "%"),
        ("Gebouwd meer dan tien jaar geleden", "ouder_dan_tien_jaar_pct", "%"),
        ("Gemiddeld gasverbruik per woning", "gas_m3", " m³"),
        ("Gemiddelde stroomlevering per woning", "stroom_kwh", " kWh"),
        ("Woningen met zonnepanelen", "zonnestroom_pct", "%"),
        ("Aardgasvrije woningen", "aardgasvrij_pct", "%"),
        ("Stadsverwarming", "stadsverwarming_pct", "%"),
        ("Hoofdzakelijk elektrisch verwarmd", "elektrisch_verwarmd_pct", "%"),
        ("Gemiddelde WOZ-waarde", "woz", " duizend euro"),
    ]
    kop = f"<tr><th></th><th>{e(wijknaam)}</th><th>{e(gemeentenaam)}</th><th>Nederland</th></tr>"
    body = "".join(vergelijk(w, g, nl, veld, eenheid).format(label=e(label)) for label, veld, eenheid in rijen if w.get(veld) is not None)
    return f'<div class="tbl"><table class="cijfers">{kop}{body}</table></div>'


def advies(w: dict, g: dict, nl: dict, naam: str) -> list[str]:
    """Regelgebaseerde duiding. Geeft alinea's terug, alleen waar de cijfers iets zeggen."""
    uit: list[str] = []
    gas, gas_nl = w.get("gas_m3"), nl.get("gas_m3")
    zon, zon_nl = w.get("zonnestroom_pct"), nl.get("zonnestroom_pct")
    oud = w.get("ouder_dan_tien_jaar_pct")
    koop = w.get("koop_pct")
    eengezins = w.get("eengezins_pct")
    stads = w.get("stadsverwarming_pct") or 0
    corporatie = w.get("corporatie_pct")

    if gas and gas_nl:
        verschil = (gas - gas_nl) / gas_nl * 100
        if stads >= 25 and verschil <= 25:
            uit.append(f"Het gasverbruik in {naam} ligt met {getal(gas)} m³ per woning onder of rond het landelijke gemiddelde van {getal(gas_nl)} m³, mede omdat {getal(stads)} procent van de woningen op stadsverwarming zit. Voor die huizen is een warmtepomp niet aan de orde. Isolatie en zonnepanelen verlagen de rekening wel, en de isolatiesubsidie geldt ook bij stadsverwarming.")
        elif verschil > 25:
            uit.append(f"Een woning in {naam} verbruikt gemiddeld {getal(gas)} m³ gas per jaar, {getal(abs(verschil))} procent meer dan het Nederlandse gemiddelde van {getal(gas_nl)} m³. Bij de huidige gasprijs is dat een verschil van enkele honderden euro's per jaar. Isolatie van dak, vloer en spouw haalt daar het meeste vanaf, en dat is ook de maatregel met de hoogste subsidie per euro.")
        elif verschil < -25:
            uit.append(f"Het gasverbruik in {naam} ligt met {getal(gas)} m³ per woning ruim onder het landelijke gemiddelde van {getal(gas_nl)} m³. Dat wijst op kleinere of nieuwere woningen, of op woningen die al van het gas af zijn. Voor wie nog wel gas stookt, is een hybride warmtepomp meestal de logische volgende stap.")
        else:
            uit.append(f"Het gasverbruik in {naam} zit met {getal(gas)} m³ per woning dicht bij het landelijke gemiddelde van {getal(gas_nl)} m³. De grootste besparing zit dan in de combinatie van isolatie en een hybride warmtepomp, waarbij de isolatiesubsidie verdubbelt.")
    if oud is not None and oud >= 95 and eengezins and eengezins >= 75 and gas and gas_nl and gas > gas_nl:
        uit.append(f"Ruim {getal(oud)} procent van de woningen is ouder dan tien jaar en {getal(eengezins)} procent is een eengezinswoning. Precies het type huis waar spouwmuur- en dakisolatie het snelst terugverdienen, vaak binnen vijf jaar.")
    if zon is not None and zon_nl is not None:
        if zon < zon_nl - 8 and koop and koop >= 50:
            uit.append(f"Slechts {getal(zon)} procent van de woningen heeft zonnepanelen, tegen {getal(zon_nl)} procent landelijk, terwijl {getal(koop)} procent koopwoning is. Er ligt hier dus veel dak ongebruikt. De btw op zonnepanelen voor woningen is nul procent, en salderen loopt nog tot en met 2026.")
        elif zon > zon_nl + 8:
            uit.append(f"Met {getal(zon)} procent woningen met zonnepanelen loopt {naam} voor op Nederland ({getal(zon_nl)} procent). Na het einde van salderen wordt een thuisbatterij hier eerder interessant, omdat overdag veel stroom wordt teruggeleverd.")
    if stads and stads >= 25 and gas and gas_nl and (gas - gas_nl) / gas_nl * 100 > 25:
        uit.append(f"{getal(stads)} procent van de woningen zit op stadsverwarming. Voor die huizen is een warmtepomp niet aan de orde, isolatie en zonnepanelen wel.")
    if corporatie is not None and corporatie >= 50:
        uit.append(f"{getal(corporatie)} procent van de woningen is van een woningcorporatie. Huurders vragen isolatie en zonnepanelen aan via de corporatie, niet via de ISDE. De cijfers hieronder gaan vooral op voor de koopwoningen in de wijk.")
    return uit


def knoppen(context: str) -> str:
    partners = CONFIG.get("partners", {})
    links = []
    for key, label in MAATREGELEN.items():
        p = partners.get(key) or {}
        if p.get("url"):
            links.append(f'<a href="{e(p["url"])}" rel="sponsored nofollow noopener" target="_blank">Offertes {e(label.lower())}</a>')
    if not links:
        return ""
    namen = sorted({(partners.get(k) or {}).get("naam") for k in MAATREGELEN if (partners.get(k) or {}).get("url")} - {None, ""})
    return f"""<h2>Offertes vergelijken</h2>
<div class="blok"><p style="margin:0 0 10px">Drie prijzen naast elkaar leggen scheelt in de praktijk het meest. Via {e(" en ".join(namen) or "onze partner")} vraag je ze in één keer aan bij bedrijven die in de buurt werken.</p>
<div class="knoppen">{"".join(links)}</div>
<p class="klein" style="margin:10px 0 0">Wij ontvangen een vergoeding als je via deze knoppen offertes aanvraagt. Dat verandert niets aan de prijs die je betaalt.</p></div>"""


def subsidietabel(kort: bool = False) -> str:
    s = SUBSIDIES
    wp = s["warmtepomp"]
    rijen = "".join(
        f'<tr><td>{e(m["naam"])}</td><td class="num">{getal(m["per_m2_enkel"], " euro")}</td><td class="num">{getal(m["per_m2_dubbel"], " euro")}</td><td class="num">{getal(m["minimum_m2"], " m²")}</td></tr>'
        for m in s["isolatie"]["maatregelen"]
    )
    return f"""<p>Warmtepomp: {getal(wp['basis'])} euro plus {getal(wp['per_kw'])} euro per kW vermogen, met {getal(wp['bonus_a_plus_plus_plus'])} euro extra bij energielabel A+++. Een toestel van 6 kW komt zo op {getal(wp['voorbeeld_6kw'])} euro, een van 10 kW op {getal(wp['voorbeeld_10kw'])} euro.</p>
<div class="tbl"><table><tr><th>Isolatie</th><th>Per m², één maatregel</th><th>Per m², twee of meer</th><th>Minimum</th></tr>{rijen}</table></div>
<p class="klein">{e(s['isolatie']['toelichting'])} Zonnepanelen: {e(s['zonnepanelen']['toelichting'])} Thuisbatterij: {e(s['thuisbatterij']['toelichting'])} Bron en actuele voorwaarden: <a href="{e(s['bron'])}" rel="noopener" target="_blank">rvo.nl</a>.</p>"""


GASPRIJS = 1.35   # euro per m³ inclusief belasting, aanpasbaar in de rekenhulp
STROOMPRIJS = 0.28

MAATREGELPAGINAS = {
    "isolatie": {
        "pad": "isolatie", "kop": "Isolatie in {g}", "cta": "isolatie",
        "titel": "Isolatie in {g}: subsidie {jaar}, besparing en offertes",
        "omschrijving": "Wat isolatie oplevert voor een woning in {g}, met de ISDE-subsidie van {jaar} en het gasverbruik per wijk.",
        "intro": "Isolatie is de maatregel met de hoogste subsidie per euro en de kortste terugverdientijd. In {g} verbruikt een woning gemiddeld {gas} m³ gas per jaar en is {oud} procent van de woningen ouder dan tien jaar. Reken hieronder uit wat spouw, dak, vloer en glas voor jouw huis schelen.",
        "kolom": ("gas_m3", " m³", "Gas per woning"),
        "uitleg": "De besparingspercentages zijn de gebruikelijke waarden van Milieu Centraal voor een niet-geïsoleerde woning: spouwmuur 20 procent, dak 15 procent, vloer 8 procent en HR++ glas 10 procent. Is een deel al gedaan, dan valt de besparing lager uit. De subsidie gaat uit van twee of meer maatregelen binnen 24 maanden, dan geldt het dubbele bedrag per m².",
    },
    "warmtepomp": {
        "pad": "warmtepomp", "kop": "Warmtepomp in {g}", "cta": "warmtepomp",
        "titel": "Warmtepomp in {g}: subsidie {jaar}, besparing en offertes",
        "omschrijving": "Wat een hybride of volledige warmtepomp oplevert in {g}, met de ISDE-subsidie van {jaar} en het gasverbruik per wijk.",
        "intro": "Een hybride warmtepomp neemt het grootste deel van het stoken over en laat de cv-ketel alleen op de koudste dagen bijspringen. In {g} verbruikt een woning gemiddeld {gas} m³ gas per jaar; {stads} procent zit op stadsverwarming en komt dus niet in aanmerking. Reken uit wat een warmtepomp bij jouw verbruik doet.",
        "kolom": ("gas_m3", " m³", "Gas per woning"),
        "uitleg": "Een hybride warmtepomp vervangt doorgaans 60 tot 70 procent van het gasverbruik voor verwarming en gebruikt daarvoor stroom, ongeveer 1 kWh per 3 kWh warmte. De rekenhulp gaat uit van 65 procent en een rendement van 3,5. Een volledige warmtepomp vervangt alles, maar vraagt goede isolatie. De subsidie is het vaste bedrag plus het bedrag per kW, zonder de bonus voor A+++.",
    },
    "zonnepanelen": {
        "pad": "zonnepanelen", "kop": "Zonnepanelen in {g}", "cta": "zonnepanelen",
        "titel": "Zonnepanelen in {g}: opbrengst, salderen en offertes",
        "omschrijving": "Wat zonnepanelen opleveren in {g}, hoeveel woningen ze al hebben en waar je offertes vergelijkt.",
        "intro": "In {g} heeft {zon} procent van de woningen zonnepanelen, landelijk is dat {zon_nl} procent. Salderen loopt tot en met 2026, daarna telt vooral wat je zelf direct verbruikt. Reken uit wat een dak vol panelen bij jouw stroomverbruik oplevert.",
        "kolom": ("zonnestroom_pct", "%", "Woningen met zonnepanelen"),
        "uitleg": "Een paneel van 430 Wp levert in Nederland ongeveer 380 kWh per jaar op een gunstig dak. De rekenhulp rekent met de stroomprijs die je invult en gaat uit van volledig salderen. Na 2026 valt de opbrengst lager uit, hoe lager naarmate je minder overdag verbruikt. Er is geen ISDE-subsidie voor zonnepanelen, wel nul procent btw.",
    },
}


def rekenhulp(maatregel: str, g: dict, nl: dict) -> str:
    sub = SUBSIDIES
    gas = int(g.get("gas_m3") or nl.get("gas_m3") or 1000)
    stroom = int(g.get("stroom_kwh") or nl.get("stroom_kwh") or 2500)
    iso = {m["naam"]: m for m in sub["isolatie"]["maatregelen"]}
    if maatregel == "isolatie":
        velden = f"""<div><label for="gas">Jouw gasverbruik per jaar (m³)</label><input id="gas" type="number" value="{gas}" min="0"></div>
<div><label for="prijs">Gasprijs (euro per m³)</label><input id="prijs" type="number" step="0.01" value="{GASPRIJS}"></div>
<div><label for="type">Woningtype</label><select id="type"><option value="tussen">Tussenwoning</option><option value="hoek">Hoekwoning</option><option value="twee">Twee-onder-een-kap</option><option value="vrij">Vrijstaand</option><option value="app">Appartement</option></select></div>"""
        uitvoer = """<div><b id="u1" class="warm">0</b><span>besparing per jaar bij spouw, dak, vloer en HR++ glas samen</span></div>
<div><b id="u2">0</b><span>ISDE-subsidie bij twee of meer maatregelen</span></div>
<div><b id="u3">0</b><span>minder gas per jaar</span></div>"""
        js = f"""var M2={{tussen:[45,50,50,18],hoek:[70,55,55,20],twee:[90,70,70,22],vrij:[130,100,90,28],app:[0,0,0,14]}};
var T=[{iso['Spouwmuurisolatie']['per_m2_dubbel']},{iso['Dakisolatie']['per_m2_dubbel']},{iso['Vloer- of bodemisolatie']['per_m2_dubbel']},{iso['HR++ glas in bestaande kozijnen']['per_m2_dubbel']}];
function reken(){{var gas=+v('gas'),p=+v('prijs'),t=v('type');var m=M2[t];var frac=(m[0]?0.20:0)+(m[1]?0.15:0)+(m[2]?0.08:0)+0.10;var minder=Math.round(gas*frac);var sub=0;for(var i=0;i<4;i++)sub+=m[i]*T[i];
z('u1',euro(minder*p));z('u2',euro(sub));z('u3',minder.toLocaleString('nl-NL')+' m³');}}"""
    elif maatregel == "warmtepomp":
        wp = sub["warmtepomp"]
        velden = f"""<div><label for="gas">Jouw gasverbruik per jaar (m³)</label><input id="gas" type="number" value="{gas}" min="0"></div>
<div><label for="prijs">Gasprijs (euro per m³)</label><input id="prijs" type="number" step="0.01" value="{GASPRIJS}"></div>
<div><label for="sprijs">Stroomprijs (euro per kWh)</label><input id="sprijs" type="number" step="0.01" value="{STROOMPRIJS}"></div>
<div><label for="type">Soort warmtepomp</label><select id="type"><option value="hybride">Hybride, 5 kW</option><option value="vol">Volledig elektrisch, 8 kW</option></select></div>"""
        uitvoer = """<div><b id="u1" class="warm">0</b><span>netto besparing per jaar</span></div>
<div><b id="u2">0</b><span>ISDE-subsidie</span></div>
<div><b id="u3">0</b><span>extra stroom per jaar</span></div>"""
        js = f"""function reken(){{var gas=+v('gas'),p=+v('prijs'),sp=+v('sprijs'),t=v('type');var deel=t==='hybride'?0.65:1.0,kw=t==='hybride'?5:8;var warmte=gas*deel*8.8;var kwh=Math.round(warmte/3.5);var besp=gas*deel*p-kwh*sp;var sub={wp['basis']}+{wp['per_kw']}*kw;
z('u1',euro(besp));z('u2',euro(sub));z('u3',kwh.toLocaleString('nl-NL')+' kWh');}}"""
    else:
        velden = f"""<div><label for="kwh">Jouw stroomverbruik per jaar (kWh)</label><input id="kwh" type="number" value="{stroom}" min="0"></div>
<div><label for="sprijs">Stroomprijs (euro per kWh)</label><input id="sprijs" type="number" step="0.01" value="{STROOMPRIJS}"></div>
<div><label for="n">Aantal panelen</label><input id="n" type="number" value="10" min="1" max="40"></div>"""
        uitvoer = """<div><b id="u1" class="warm">0</b><span>opbrengst per jaar bij salderen</span></div>
<div><b id="u2">0</b><span>kWh per jaar uit de panelen</span></div>
<div><b id="u3">0</b><span>van je verbruik gedekt</span></div>"""
        js = """function reken(){var kwh=+v('kwh'),sp=+v('sprijs'),n=+v('n');var op=n*380;var dek=kwh?Math.min(100,Math.round(op/kwh*100)):0;
z('u1',euro(Math.min(op,kwh*1.0)*sp+Math.max(0,op-kwh)*0.05));z('u2',op.toLocaleString('nl-NL')+' kWh');z('u3',dek+'%');}"""
    return f"""<div class="reken">
<div class="velden">{velden}</div>
<div class="uit">{uitvoer}</div>
<p class="klein">Schatting op basis van gemiddelden, geen offerte. De gemeentecijfers staan voor-ingevuld, vul je eigen jaarafrekening in voor een beter beeld.</p>
</div>
<script>
(function(){{function v(id){{return document.getElementById(id).value;}}function z(id,t){{document.getElementById(id).textContent=t;}}
function euro(x){{return Math.round(x).toLocaleString('nl-NL')+' euro';}}
{js}
document.querySelectorAll('.reken input,.reken select').forEach(function(el){{el.addEventListener('input',reken);}});reken();}})();
</script>"""


def bouw_maatregelpaginas(gemeenten: dict, gem_slugs: dict, wijken_per_gemeente: dict, nl: dict, uit: str, wijknaam) -> list[str]:
    urls = []
    for gm, g in gemeenten.items():
        gslug = gem_slugs[gm]
        gnaam = g["gemeente"]
        wijken = wijken_per_gemeente.get(gm, [])
        for key, c in MAATREGELPAGINAS.items():
            veld, eenheid, kolomkop = c["kolom"]
            rijen = sorted([w for w in wijken if w.get(veld) is not None], key=lambda w: -w[veld])
            wijktabel = ""
            if rijen:
                wijktabel = f'<h2>Per wijk in {e(gnaam)}</h2><div class="tbl"><table><tr><th>Wijk</th><th>{e(kolomkop)}</th><th>Koop</th><th>Ouder dan 10 jaar</th></tr>' + "".join(
                    f'<tr><td><a href="../{slugify(wijknaam(w["code"]))}/">{e(wijknaam(w["code"]))}</a></td><td class="num">{getal(w.get(veld), eenheid)}</td><td class="num">{getal(w.get("koop_pct"), "%")}</td><td class="num">{getal(w.get("ouder_dan_tien_jaar_pct"), "%")}</td></tr>'
                    for w in rijen) + "</table></div>"
            ctx = dict(g=gnaam, jaar=SUBSIDIES["jaar"], gas=getal(g.get("gas_m3")), oud=getal(g.get("ouder_dan_tien_jaar_pct")),
                       stads=getal(g.get("stadsverwarming_pct") or 0), zon=getal(g.get("zonnestroom_pct")), zon_nl=getal(nl.get("zonnestroom_pct")))
            partners = CONFIG.get("partners", {})
            p = partners.get(c["cta"]) or {}
            cta = ""
            if p.get("url"):
                cta = f"""<h2>Offertes vergelijken</h2><div class="blok"><p style="margin:0 0 10px">Drie prijzen naast elkaar leggen scheelt in de praktijk het meest. Via {e(p.get('naam') or 'onze partner')} vraag je ze in één keer aan bij bedrijven die in {e(gnaam)} werken.</p>
<div class="knoppen"><a href="{e(p['url'])}" rel="sponsored nofollow noopener" target="_blank">Vraag drie offertes aan</a></div>
<p class="klein" style="margin:10px 0 0">Wij ontvangen een vergoeding als je via deze knop offertes aanvraagt. Dat verandert niets aan de prijs die je betaalt.</p></div>"""
            andere = " ".join(f'<a href="../{o["pad"]}/">{e(o["kop"].format(g=gnaam))}</a>' for k, o in MAATREGELPAGINAS.items() if k != key)
            body = f"""<h1>{e(c['kop'].format(**ctx))}</h1>
<p class="lead">{e(c['intro'].format(**ctx))}</p>
<h2>Reken het uit voor jouw huis</h2>
{rekenhulp(key, g, nl)}
<p class="klein">{e(c['uitleg'])}</p>
{cta}
{wijktabel}
<h2>Subsidie in {SUBSIDIES['jaar']}</h2>
{subsidietabel()}
<p class="klein">Ook interessant: {andere}. Alle cijfers van {e(gnaam)}: <a href="../">energie per wijk in {e(gnaam)}</a>.</p>"""
            os.makedirs(os.path.join(uit, gslug, c["pad"]), exist_ok=True)
            with open(os.path.join(uit, gslug, c["pad"], "index.html"), "w", encoding="utf-8") as f:
                f.write(pagina(c["titel"].format(**ctx), body, 2, c["omschrijving"].format(**ctx), f"{gslug}/{c['pad']}/"))
            urls.append(f"{gslug}/{c['pad']}/")
    return urls


def bouw_site(rijen: list[dict], namen: dict, uit: str, vandaag: dt.date, bronnen: dict | None = None) -> dict:
    global BRONTEKST
    BRONTEKST = brontekst(bronnen)
    nl = next((r for r in rijen if r["code"] == "NL00"), {})
    gemeenten = {r["code"]: r for r in rijen if r["soort"] == "gemeente"}
    wijken_per_gemeente: dict[str, list[dict]] = defaultdict(list)
    for r in rijen:
        if r["soort"] == "wijk" and r.get("woningen") and r["woningen"] >= 200:
            gm = next((c for c, g in gemeenten.items() if g["gemeente"] == r["gemeente"]), None)
            if gm:
                wijken_per_gemeente[gm].append(r)

    os.makedirs(uit, exist_ok=True)
    os.makedirs(os.path.join(uit, "data"), exist_ok=True)
    urls: list[str] = []

    # Wijknaam opschonen: "Wijk 00 Annen" -> "Annen"
    def wijknaam(code: str) -> str:
        n = namen.get(code, code)
        import re
        n = re.sub(r"^Wijk\s+\d+\s*", "", n).strip()
        return n or namen.get(code, code)

    # Gemeente- en wijkpagina's
    gem_slugs: dict[str, str] = {}
    zoekdata: list[list] = []
    alle_wijken: list[tuple[dict, str, str, str]] = []
    for gm, g in sorted(gemeenten.items(), key=lambda kv: kv[1]["gemeente"]):
        gnaam = g["gemeente"]
        gslug = slugify(gnaam)
        gem_slugs[gm] = gslug
        wijken = sorted(wijken_per_gemeente.get(gm, []), key=lambda w: (w.get("gas_m3") is None, -(w.get("gas_m3") or 0)))
        os.makedirs(os.path.join(uit, gslug), exist_ok=True)
        wijkrijen = []
        wijkslugs = {}
        for w in wijken:
            wnaam = wijknaam(w["code"])
            wslug = slugify(wnaam)
            if wslug in wijkslugs:
                wslug = f"{wslug}-{w['code'].lower().strip()}"
            wijkslugs[wslug] = w
            alle_wijken.append((w, wnaam, gnaam, f"{gslug}/{wslug}/"))
            wijkrijen.append(f'<tr><td><a href="{wslug}/">{e(wnaam)}</a></td><td class="num">{getal(w.get("woningen"))}</td><td class="num">{getal(w.get("gas_m3"), " m³")}</td><td class="num">{getal(w.get("zonnestroom_pct"), "%")}</td><td class="num">{getal(w.get("koop_pct"), "%")}</td><td class="num">{getal(w.get("ouder_dan_tien_jaar_pct"), "%")}</td></tr>')
                # Wijkpagina
            os.makedirs(os.path.join(uit, gslug, wslug), exist_ok=True)
            alineas = advies(w, g, nl, wnaam)
            body = f"""<h1>Energie in {e(wnaam)}, {e(gnaam)}</h1>
<p class="lead">{getal(w.get('woningen'))} woningen, {getal(w.get('koop_pct'), '%')} koop. Gemiddeld {getal(w.get('gas_m3'))} m³ gas en {getal(w.get('stroom_kwh'))} kWh stroom per woning per jaar, {getal(w.get('zonnestroom_pct'), '%')} van de woningen heeft zonnepanelen.{(' Postcode ' + e(w.get('postcode'))) + '.' if w.get('postcode') else ''}</p>
<div class="advies">{"".join(f"<p>{e(a)}</p>" for a in alineas)}</div>
<h2>De cijfers naast elkaar</h2>
<div class="tweekolom">
{staven("Gasverbruik per woning per jaar", [(wnaam, w.get("gas_m3"), True), (gnaam, g.get("gas_m3"), False), ("Nederland", nl.get("gas_m3"), False)], " m³")}
{staven("Woningen met zonnepanelen", [(wnaam, w.get("zonnestroom_pct"), True), (gnaam, g.get("zonnestroom_pct"), False), ("Nederland", nl.get("zonnestroom_pct"), False)], "%", "zon")}
</div>
{cijfertabel(w, g, nl, wnaam, gnaam)}
<h2>Subsidie in {SUBSIDIES['jaar']}</h2>
{subsidietabel()}
{knoppen(f"wijk:{gnaam}/{wnaam}")}
<p class="maatregelen">Reken het uit voor jouw huis: {" ".join(f'<a href="../{c["pad"]}/">{e(c["kop"].format(g=gnaam))}</a>' for c in MAATREGELPAGINAS.values())}</p>
<p class="klein">Verbouwen in {e(gnaam)}? Bekijk de <a href="{VERGUNNINGEN_URL}{gslug}/">recente bouwvergunningen in {e(gnaam)}</a> op Vergunningenradar. Andere wijken: <a href="../">{e(gnaam)}</a>.</p>"""
            with open(os.path.join(uit, gslug, wslug, "index.html"), "w", encoding="utf-8") as f:
                f.write(pagina(f"Energie in {wnaam} ({gnaam}): gasverbruik, zonnepanelen en subsidie {SUBSIDIES['jaar']}", body, 2,
                               f"Gasverbruik, stroom, zonnepanelen en woningtype in {wnaam}, {gnaam}, vergeleken met de gemeente en Nederland. Met de ISDE-subsidie van {SUBSIDIES['jaar']}.", f"{gslug}/{wslug}/"))
            urls.append(f"{gslug}/{wslug}/")
        alineas_g = advies(g, g, nl, gnaam) if not wijken else []
        body = f"""<h1>Energie per wijk in {e(gnaam)}</h1>
<p class="lead">{getal(g.get('woningen'))} woningen in {len(wijken)} wijken. Gemiddeld {getal(g.get('gas_m3'))} m³ gas per woning (Nederland {getal(nl.get('gas_m3'))} m³), {getal(g.get('zonnestroom_pct'), '%')} van de woningen heeft zonnepanelen, {getal(g.get('aardgasvrij_pct'), '%')} is aardgasvrij.</p>
<div class="advies">{"".join(f"<p>{e(a)}</p>" for a in alineas_g)}</div>
<p class="maatregelen">Wat wil je doen? {" ".join(f'<a href="{c["pad"]}/">{e(c["kop"].format(g=gnaam))}</a>' for c in MAATREGELPAGINAS.values())}</p>
<h2>Wijken, gesorteerd op gasverbruik</h2>
<div class="filter"><input id="filter" placeholder="Zoek een wijk in {e(gnaam)}" aria-label="Wijk zoeken"></div>
<div class="tbl"><table class="wijken"><thead><tr><th>Wijk</th><th>Woningen</th><th>Gas per woning</th><th>Zonnepanelen</th><th>Koop</th><th>Ouder dan 10 jaar</th></tr></thead><tbody>{"".join(wijkrijen)}</tbody></table></div>
{FILTER_JS}
{knoppen(f"gemeente:{gnaam}")}
<p class="klein">Bekijk ook de <a href="{VERGUNNINGEN_URL}{gslug}/">recente bouwvergunningen in {e(gnaam)}</a> op Vergunningenradar.</p>"""
        with open(os.path.join(uit, gslug, "index.html"), "w", encoding="utf-8") as f:
            f.write(pagina(f"Energie per wijk in {gnaam}: gasverbruik, zonnepanelen en subsidie", body, 1,
                           f"Gasverbruik, zonnepanelen en aardgasvrije woningen per wijk in {gnaam}, met de ISDE-subsidie van {SUBSIDIES['jaar']}.", f"{gslug}/"))
        urls.append(f"{gslug}/")
        with open(os.path.join(uit, "data", f"{gslug}.json"), "w", encoding="utf-8") as f:
            json.dump({"gemeente": g, "wijken": wijken}, f, ensure_ascii=False, separators=(",", ":"))

    maatregel_urls = bouw_maatregelpaginas(gemeenten, gem_slugs, wijken_per_gemeente, nl, uit, wijknaam)
    urls.extend(maatregel_urls)

    # Overzicht
    for gm, g in gemeenten.items():
        zoekdata.append([g["gemeente"], "", f"{gem_slugs[gm]}/"])
        for key, c in MAATREGELPAGINAS.items():
            zoekdata.append([c["kop"].format(g=g["gemeente"]), "", f"{gem_slugs[gm]}/{c['pad']}/"])
    for w, wn, gn, pad in alle_wijken:
        zoekdata.append([wn, gn, pad])
    zoekdata.sort(key=lambda r: (r[1] != "", r[0]))
    links = "".join(f'<div><a href="{gem_slugs[gm]}/">{e(g["gemeente"])}</a> <span class="n">{getal(g.get("gas_m3"))} m³</span></div>'
                    for gm, g in sorted(gemeenten.items(), key=lambda kv: kv[1]["gemeente"]))
    grote = [x for x in alle_wijken if (x[0].get("woningen") or 0) >= 1000 and x[0].get("gas_m3")]
    meeste_gas = sorted(grote, key=lambda x: -x[0]["gas_m3"])[:8]
    meeste_zon = sorted([x for x in grote if x[0].get("zonnestroom_pct") is not None], key=lambda x: -x[0]["zonnestroom_pct"])[:8]
    def toprij(x, veld, eenheid):
        w, wn, gn, pad = x
        return f'<tr><td><a href="{pad}">{e(wn)}</a> <span class="klein">{e(gn)}</span></td><td class="num">{getal(w.get(veld), eenheid)}</td></tr>'
    body = f"""<div class="hero">
<h1>Hoeveel gas verbruikt jouw wijk?</h1>
<p class="lead">Zoek je wijk en zie in één oogopslag hoe jouw buurt ervoor staat: gasverbruik, zonnepanelen, woningtype en de subsidie die je in {SUBSIDIES['jaar']} kunt krijgen. Cijfers van het CBS, voor alle {len(alle_wijken)} wijken van Nederland.</p>
<div class="zoek"><input id="zoek" type="search" placeholder="Typ je wijk of gemeente, bijvoorbeeld Brouwhuis of Helmond" autocomplete="off" aria-label="Zoek wijk of gemeente"><ul id="zoekres"></ul></div>
</div>
<div class="kern">
<div><b class="groot">{getal(nl.get('gas_m3'))} m³</b><span>gas per woning per jaar, landelijk gemiddelde</span></div>
<div><b>{getal(nl.get('zonnestroom_pct'), '%')}</b><span>van de woningen heeft zonnepanelen</span></div>
<div><b>{getal(nl.get('aardgasvrij_pct'), '%')}</b><span>van de woningen is aardgasvrij</span></div>
</div>
<div class="tweekolom">
<div><h2>Wijken met het hoogste gasverbruik</h2><div class="tbl"><table class="toplijst">{"".join(toprij(x, "gas_m3", " m³") for x in meeste_gas)}</table></div><p class="klein">Wijken met minstens 1000 woningen.</p></div>
<div><h2>Wijken met de meeste zonnepanelen</h2><div class="tbl"><table class="toplijst">{"".join(toprij(x, "zonnestroom_pct", "%") for x in meeste_zon)}</table></div><p class="klein">Aandeel woningen met zonnestroom.</p></div>
</div>
<h2>Alle gemeenten</h2>
<p class="klein">Met het gemiddelde gasverbruik per woning. Per gemeente vind je ook een rekenhulp voor isolatie, een warmtepomp en zonnepanelen.</p>
<div class="kolommen">{links}</div>
<p class="klein" style="margin-top:24px">{e(BRONTEKST)} Bijgewerkt op {e(datum_nl(vandaag.isoformat()))}.</p>
<script id="zoekdata" type="application/json">{json.dumps(zoekdata, ensure_ascii=False, separators=(",", ":"))}</script>
{ZOEK_JS}"""
    with open(os.path.join(uit, "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina("Energie per wijk: gasverbruik, zonnepanelen en subsidie per gemeente", body, 0,
                       "Gasverbruik, stroom en zonnepanelen per wijk voor alle Nederlandse gemeenten, met de ISDE-subsidie.", ""))

    # Subsidiepagina
    with open(os.path.join(uit, "subsidie.html"), "w", encoding="utf-8") as f:
        f.write(pagina(f"ISDE-subsidie {SUBSIDIES['jaar']}: bedragen voor warmtepomp en isolatie", f"<h1>ISDE-subsidie {SUBSIDIES['jaar']}</h1><p class=\"lead\">De landelijke subsidie voor isolatie, warmtepompen en zonneboilers in bestaande woningen. Je vraagt hem aan bij RVO na de installatie, met factuur en betaalbewijs.</p>{subsidietabel()}{knoppen('subsidie')}", 0,
                       f"Alle ISDE-bedragen van {SUBSIDIES['jaar']} voor warmtepomp, isolatie en glas op een rij.", "subsidie.html"))

    with open(os.path.join(uit, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in ["", "subsidie.html", "over.html"] + urls:
            f.write(f"<url><loc>{BASIS_URL}{e(u)}</loc><lastmod>{vandaag.isoformat()}</lastmod></url>\n")
        f.write("</urlset>\n")
    return {"gemeenten": len(gemeenten), "wijken": sum(len(v) for v in wijken_per_gemeente.values())}

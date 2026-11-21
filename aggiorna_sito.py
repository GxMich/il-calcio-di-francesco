"""
Aggiorna il sito "Il Calcio di Francesco".

Cosa fa:
  1. scarica i risultati della Serie A dall'API gratuita TheSportsDB
     (https://www.thesportsdb.com, chiave pubblica "123", nessuna registrazione)
  2. scarica la classifica, gli stemmi delle squadre e le foto dei calciatori
     (foto da Wikipedia / Wikimedia Commons, con licenza libera)
  3. mette tutto dentro un unico file: index.html

Come si usa (da PowerShell, dentro questa cartella):
    python aggiorna_sito.py

Poi apri index.html con il browser.
"""

import datetime as dt
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path

try:  # Pillow serve per rimpicciolire le immagini e creare le icone (pip install pillow)
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

QUI = Path(__file__).resolve().parent
CACHE = QUI / "cache"
CACHE.mkdir(exist_ok=True)
IMG = QUI / "img"

API = "https://www.thesportsdb.com/api/v1/json/123"
LEGA = 4332  # Serie A
UA = {"User-Agent": "sito-calcio-ragazzi/1.0"}
OGGI = dt.date.today()
PARTITE_DA_MOSTRARE = 100

NOMI_ITALIANI = {"AC Milan": "Milan", "Inter Milan": "Inter", "Hellas Verona": "Verona"}


def nome(squadra):
    return NOMI_ITALIANI.get(squadra, squadra)


def scarica(url, binario=False, tentativi=6):
    """Scarica un URL. Se il server dice 'troppe richieste', aspetta e riprova."""
    for i in range(tentativi):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                dati = r.read()
            if binario:
                return dati
            testo = dati.decode("utf-8")
            if testo.startswith("error code"):
                raise RuntimeError(testo.strip())
            return testo
        except Exception as e:  # noqa: BLE001
            attesa = 20 * (i + 1)
            print(f"   ...aspetto {attesa}s ({e})")
            time.sleep(attesa)
    raise RuntimeError(f"Non riesco a scaricare {url}")


def api(percorso, file_cache, valido_per_giorni=0):
    """Chiama l'API usando la cache: i dati vecchi e definitivi non si riscaricano."""
    f = CACHE / file_cache
    if f.exists() and valido_per_giorni:
        eta = (time.time() - f.stat().st_mtime) / 86400
        if eta < valido_per_giorni:
            return json.loads(f.read_text(encoding="utf-8"))
    testo = scarica(f"{API}/{percorso}")
    f.write_text(testo, encoding="utf-8")
    time.sleep(2.5)  # la chiave gratuita accetta poche richieste al minuto
    return json.loads(testo)


def stagione_corrente():
    anno = OGGI.year if OGGI.month >= 7 else OGGI.year - 1
    return f"{anno}-{anno + 1}"


def stagione_precedente(s):
    a = int(s[:4]) - 1
    return f"{a}-{a + 1}"


def giornata(stagione, r):
    f = CACHE / f"{stagione}_g{r}.json"
    if f.exists():
        eventi = json.loads(f.read_text(encoding="utf-8")).get("events") or []
        finite = eventi and all(e.get("intHomeScore") is not None for e in eventi)
        if finite and all(e["dateEvent"] < (OGGI - dt.timedelta(days=3)).isoformat() for e in eventi):
            return eventi  # giornata chiusa: non serve riscaricarla
    print(f" - {stagione}, giornata {r}")
    return api(f"eventsround.php?id={LEGA}&r={r}&s={stagione}", f"{stagione}_g{r}.json").get("events") or []


def converti(e):
    return {
        "id": e["idEvent"],
        "stagione": e["strSeason"],
        "giornata": int(e["intRound"] or 0),
        "data": e["dateEvent"],
        "ora": (e.get("strTimeLocal") or e.get("strTime") or "")[:5],
        "casa": nome(e["strHomeTeam"]),
        "ospiti": nome(e["strAwayTeam"]),
        "gc": None if e["intHomeScore"] is None else int(e["intHomeScore"]),
        "go": None if e["intAwayScore"] is None else int(e["intAwayScore"]),
        "stadio": e.get("strVenue") or "",
        "video": e.get("strVideo") or "",
        "rinviata": (e.get("strPostponed") or "no") == "yes",
        "_stemmi": {nome(e["strHomeTeam"]): e.get("strHomeTeamBadge"), nome(e["strAwayTeam"]): e.get("strAwayTeamBadge")},
    }


def slug(testo):
    testo = unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", testo).strip("-").lower()


def immagine(url, percorso, lato, jpeg=False):
    """Scarica un'immagine una volta sola dentro img/, la rimpicciolisce e
    restituisce il percorso da usare nella pagina."""
    f = IMG / percorso
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        dati = scarica(url, binario=True)
        time.sleep(1)
        if Image:
            im = Image.open(BytesIO(dati))
            im.thumbnail((lato, lato))
            if jpeg:
                im.convert("RGB").save(f, "JPEG", quality=80, optimize=True, progressive=True)
            else:
                im.save(f, "PNG", optimize=True)
        else:
            f.write_bytes(dati)
    return "img/" + percorso


# ---------- Esultanze famose ----------
ESULTANZE = [
    dict(giocatore="Cristiano Ronaldo", wiki="Cristiano_Ronaldo", paese="Portogallo", mossa="Il «Siuuu!»",
         storia="La esultanza più imitata del mondo. Ronaldo corre, salta girandosi in aria e atterra a gambe larghe. Tutto lo stadio urla con lui: «Siuuu!», che in spagnolo vuol dire «sì!».",
         passi=["Corri verso la bandierina", "Salta e fai mezzo giro in aria", "Atterra a gambe larghe, braccia tese verso il basso", "Urla «SIUUU!»"],
         video="Cristiano Ronaldo Siuuu celebration"),
    dict(giocatore="Kylian Mbappé", wiki="Kylian_Mbappé", paese="Francia", mossa="Braccia incrociate",
         storia="Mbappé si ferma serio serio con le braccia incrociate, come un supereroe. L'ha copiata dal fratellino Ethan, che la faceva quando lo batteva ai videogiochi di calcio.",
         passi=["Corri e poi fermati di colpo", "Incrocia le braccia sul petto", "Faccia seria, sguardo lontano", "Resta immobile come una statua"],
         video="Mbappé celebration arms crossed"),
    dict(giocatore="Erling Haaland", wiki="Erling_Haaland", paese="Norvegia", mossa="La meditazione",
         storia="Il gigante norvegese, dopo il gol, si siede a gambe incrociate con le mani sulle ginocchia e gli occhi chiusi. Calmo come un monaco, mentre lo stadio impazzisce.",
         passi=["Siediti per terra", "Incrocia le gambe", "Mani aperte sulle ginocchia", "Chiudi gli occhi e respira: ommm"],
         video="Haaland meditation celebration"),
    dict(giocatore="Lionel Messi", wiki="Lionel_Messi", paese="Argentina", mossa="Due dita al cielo",
         storia="Messi indica il cielo con tutte e due le mani. Dedica ogni gol a nonna Celia, che da piccolo lo accompagnava agli allenamenti.",
         passi=["Guarda in alto", "Alza le braccia", "Indica il cielo con gli indici", "Pensa a una persona a cui vuoi bene"],
         video="Messi celebration pointing to the sky"),
    dict(giocatore="Paulo Dybala", wiki="Paulo_Dybala", paese="Argentina", mossa="La Dybala Mask",
         storia="Dybala mette la mano davanti al viso come la maschera di un gladiatore: pollice e indice formano una «L» sotto gli occhi. Vuol dire: nei momenti difficili si combatte con coraggio.",
         passi=["Apri pollice e indice a forma di L", "Appoggia la mano sotto gli occhi", "Lo sguardo da gladiatore", "Corri verso i tifosi"],
         video="Dybala mask celebration"),
    dict(giocatore="Jude Bellingham", wiki="Jude_Bellingham", paese="Inghilterra", mossa="Braccia spalancate",
         storia="Bellingham si ferma davanti ai tifosi a braccia aperte, petto in fuori e sorriso. I tifosi del Real Madrid gli cantano «Hey Jude», la canzone dei Beatles.",
         passi=["Corri davanti alla curva", "Fermati a piedi uniti", "Apri le braccia più che puoi", "Petto in fuori e sorriso"],
         video="Jude Bellingham celebration arms wide"),
    dict(giocatore="Antoine Griezmann", wiki="Antoine_Griezmann", paese="Francia", mossa="Il balletto della L",
         storia="Griezmann fa un balletto preso dal videogioco Fortnite: mano a forma di L sulla fronte e saltelli da una gamba all'altra. L'ha fatto anche ai Mondiali del 2018, che la Francia ha vinto.",
         passi=["Mano a L sulla fronte", "Saltella su una gamba", "Cambia gamba a tempo", "Sorridi alla telecamera"],
         video="Griezmann Take the L celebration"),
    dict(giocatore="Francesco Totti", wiki="Francesco_Totti", paese="Italia · Roma", mossa="Il selfie e il pollice in bocca",
         storia="Nel derby del 2015 Totti segna, prende un telefono e si fa un selfie con la curva della Roma dietro. Quando sono nati i suoi figli, invece, esultava con il pollice in bocca.",
         passi=["Corri verso i tuoi tifosi", "Girati di spalle", "Alza un telefono immaginario", "Clic! Selfie con tutto lo stadio"],
         video="Totti selfie derby 2015"),
    dict(giocatore="Alessandro Del Piero", wiki="Alessandro_Del_Piero", paese="Italia · Juventus", mossa="La linguaccia",
         storia="Del Piero, capitano della Juventus per tanti anni, correva verso i tifosi con la lingua di fuori e le braccia larghe. Una linguaccia diventata famosa in tutta Italia.",
         passi=["Corri a braccia larghe", "Tira fuori la lingua", "Guarda i tifosi", "Non fermarti finché non ti abbracciano"],
         video="Del Piero linguaccia esultanza"),
    dict(giocatore="Marco Tardelli", wiki="Marco_Tardelli", paese="Italia", mossa="L'urlo di Tardelli",
         storia="Finale dei Mondiali 1982, Italia contro Germania. Tardelli segna e corre urlando, scuotendo la testa con i pugni stretti. È l'urlo più famoso della storia del calcio italiano.",
         passi=["Corri a pugni chiusi", "Scuoti la testa", "Urla con tutto il fiato", "Non smettere di correre"],
         video="Tardelli urlo 1982"),
    dict(giocatore="Bebeto", wiki="Bebeto", paese="Brasile", mossa="Il bambino in braccio",
         storia="Mondiali 1994: Bebeto segna e, insieme ai compagni, finge di cullare un neonato. Suo figlio era nato due giorni prima. Oggi lo fanno tutti i calciatori quando diventano papà.",
         passi=["Unisci le braccia davanti alla pancia", "Fai dondolare a destra e sinistra", "Chiama due compagni", "Cullate tutti insieme"],
         video="Bebeto rocking baby celebration 1994"),
    dict(giocatore="Paul Pogba", wiki="Paul_Pogba", paese="Francia", mossa="Il dab",
         storia="Pogba ha portato nel calcio il «dab», un passo di danza: la testa si nasconde nel gomito e l'altro braccio si allunga in diagonale.",
         passi=["Piega un braccio davanti alla faccia", "Nascondi il naso nel gomito", "Allunga l'altro braccio in alto", "Tieni la posa un secondo"],
         video="Pogba dab celebration"),
    dict(giocatore="Roger Milla", wiki="Roger_Milla", paese="Camerun", mossa="Il ballo della bandierina",
         storia="Mondiali 1990, proprio in Italia! Milla aveva 38 anni e dopo ogni gol ballava muovendo i fianchi attorno alla bandierina del calcio d'angolo. Il mondo intero si è messo a ballare con lui.",
         passi=["Corri alla bandierina", "Una mano sulla pancia, una in alto", "Muovi i fianchi a ritmo", "Gira attorno alla bandierina"],
         video="Roger Milla corner flag dance 1990"),
    dict(giocatore="Peter Crouch", wiki="Peter_Crouch", paese="Inghilterra", mossa="Il robot",
         storia="Crouch era altissimo, quasi due metri. Dopo il gol ballava a scatti come un robot, con le braccia rigide. Diceva che lo faceva solo quando segnava gol importanti.",
         passi=["Braccia rigide a 90 gradi", "Muovi un braccio alla volta a scatti", "Gambe dritte, passi meccanici", "Faccia seria: sei una macchina!"],
         video="Peter Crouch robot dance"),
]


def foto_wikipedia(titolo):
    """Foto del calciatore da Wikipedia (sempre con licenza libera) + crediti."""
    f = CACHE / f"wiki_{slug(titolo)}.json"
    if not f.exists():
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(titolo)
        f.write_text(scarica(url), encoding="utf-8")
        time.sleep(1.5)
    info = json.loads(f.read_text(encoding="utf-8"))
    sorgente = (info.get("originalimage") or {}).get("source")
    if not sorgente:
        return None, None
    nome_file = urllib.parse.unquote(sorgente.split("/")[-1].split("?")[0])
    meta_f = CACHE / f"commons_{slug(titolo)}.json"
    if not meta_f.exists():
        q = urllib.parse.urlencode({"action": "query", "titles": "File:" + nome_file, "prop": "imageinfo",
                                    "iiprop": "url|extmetadata", "iiurlwidth": 960, "format": "json"})
        meta_f.write_text(scarica("https://commons.wikimedia.org/w/api.php?" + q), encoding="utf-8")
        time.sleep(2)
    pagine = json.loads(meta_f.read_text(encoding="utf-8"))["query"]["pages"]
    ii = next(iter(pagine.values()))["imageinfo"][0]
    em = ii.get("extmetadata", {})
    autore = em.get("Artist", {}).get("value", "")
    # togli i tag HTML dall'autore
    autore = re.sub(r"<[^>]+>", "", autore).strip() or "autore sconosciuto"
    licenza = em.get("LicenseShortName", {}).get("value", "")
    credito = {"autore": autore[:80], "licenza": licenza, "pagina": ii.get("descriptionurl", "")}
    # 720 px: nitida anche sugli schermi Retina dell'iPhone, ma leggera
    return immagine(ii["thumburl"], f"calciatori/{slug(titolo)}.jpg", 720, jpeg=True), credito


def disegna_pallone(d, cx, cy, r):
    """Pallone semplice: cerchio bianco, pentagono nero al centro e cuciture."""
    import math
    w = max(2, r // 10)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="white", outline="#11261a", width=w)
    pent = [(cx + r * 0.4 * math.cos(math.radians(-90 + 72 * i)), cy + r * 0.4 * math.sin(math.radians(-90 + 72 * i))) for i in range(5)]
    for x, y in pent:
        dx, dy = x - cx, y - cy
        d.line([(x, y), (cx + dx * 2.45, cy + dy * 2.45)], fill="#11261a", width=w)
    d.polygon(pent, fill="#11261a")


def font(nomi, dimensione):
    for n in nomi:
        try:
            return ImageFont.truetype(n, dimensione)
        except OSError:
            continue
    return ImageFont.load_default(size=dimensione)


def crea_icone():
    """Icone per «Aggiungi a Home» (iPhone/Android) e anteprima per WhatsApp. Solo se mancano."""
    if not Image:
        return
    verde, verde2 = "#1d7a3c", "#19703a"
    for nome_file, lato in (("apple-touch-icon.png", 180), ("icona-192.png", 192), ("icona-512.png", 512)):
        f = QUI / nome_file
        if f.exists():
            continue
        g = 1024
        im = Image.new("RGB", (g, g), verde)
        d = ImageDraw.Draw(im)
        for i in range(0, g, 128):
            d.rectangle([i + 64, 0, i + 127, g], fill=verde2)
        disegna_pallone(d, g // 2, g // 2, int(g * 0.33))
        im.resize((lato, lato), Image.LANCZOS).save(f, "PNG", optimize=True)
    f = QUI / "anteprima.png"
    if not f.exists():
        im = Image.new("RGB", (1200, 630), verde)
        d = ImageDraw.Draw(im)
        for i in range(0, 1200, 120):
            d.rectangle([i + 60, 0, i + 119, 630], fill=verde2)
        d.rectangle([0, 600, 1200, 630], fill="white")
        disegna_pallone(d, 1000, 300, 150)
        grosso = font(["ariblk.ttf", "C:/Windows/Fonts/ariblk.ttf", "DejaVuSans-Bold.ttf"], 84)
        medio = font(["arialbd.ttf", "C:/Windows/Fonts/arialbd.ttf", "DejaVuSans-Bold.ttf"], 40)
        for y, riga in ((150, "IL CALCIO"), (250, "DI FRANCESCO")):
            d.text((74, y + 6), riga, font=grosso, fill="#0f3d1f")
            d.text((70, y), riga, font=grosso, fill="white")
        d.text((72, 390), "Serie A: risultati, classifica", font=medio, fill="#ffcf1a")
        d.text((72, 445), "ed esultanze famose", font=medio, fill="#ffcf1a")
        im.save(f, "PNG", optimize=True)


def main():
    stagione = stagione_corrente()
    print(f"Scarico la Serie A {stagione}...")

    partite = []
    for r in range(1, 39):
        eventi = giornata(stagione, r)
        if not eventi:
            break
        partite += [converti(e) for e in eventi]
        if all(e["intHomeScore"] is None for e in eventi):
            break  # questa è la prossima giornata: le successive non sono ancora giocate

    giocate = [p for p in partite if p["gc"] is not None]
    if len(giocate) < PARTITE_DA_MOSTRARE:  # inizio stagione: prendo anche la stagione prima
        prec = stagione_precedente(stagione)
        r = 38
        while len(giocate) < PARTITE_DA_MOSTRARE and r > 0:
            extra = [converti(e) for e in giornata(prec, r)]
            partite = extra + partite
            giocate = [p for p in partite if p["gc"] is not None]
            r -= 1

    print("Scarico la classifica...")
    tabella = api(f"lookuptable.php?l={LEGA}&s={stagione}", f"{stagione}_classifica.json").get("table") or []

    print("Scarico gli stemmi...")
    stemmi_url = {}
    for p in partite:
        for k, v in p.pop("_stemmi").items():
            if v:
                stemmi_url[k] = v
    stemmi = {}
    for squadra, url in sorted(stemmi_url.items()):
        # versione "small" (250 px) ridotta a 128 px: nitida sugli schermi Retina
        stemmi[squadra] = immagine(url + "/small", f"stemmi/{slug(squadra)}.png", 128)

    # La chiave gratuita dà solo le prime 5 della classifica: la calcoliamo noi
    # da tutte le partite della stagione, e la confrontiamo con quella dell'API.
    righe = {}
    for p in partite:
        if p["stagione"] != stagione or p["gc"] is None:
            continue
        for sq, fatti, subiti in ((p["casa"], p["gc"], p["go"]), (p["ospiti"], p["go"], p["gc"])):
            r = righe.setdefault(sq, {"squadra": sq, "g": 0, "v": 0, "n": 0, "p": 0, "gf": 0, "gs": 0})
            r["g"] += 1
            r["gf"] += fatti
            r["gs"] += subiti
            r["v" if fatti > subiti else "n" if fatti == subiti else "p"] += 1
    for r in righe.values():
        r["punti"] = 3 * r["v"] + r["n"]
        r["dr"] = r["gf"] - r["gs"]
    classifica = sorted(righe.values(), key=lambda r: (-r["punti"], -r["dr"], -r["gf"], r["squadra"]))
    for i, r in enumerate(classifica, 1):
        r["pos"] = i
        r["zona"] = ("champions" if i <= 4 else "europa" if i == 5 else "conference" if i == 6
                     else "retrocessione" if i > len(classifica) - 3 else "")
    for t in tabella:
        mia = next((r for r in classifica if r["squadra"] == nome(t["strTeam"])), None)
        if mia and mia["punti"] != int(t["intPoints"]):
            print(f"   attenzione: {mia['squadra']} ha {mia['punti']} punti per noi, {t['intPoints']} per l'API")

    print("Scarico le foto dei calciatori...")
    esultanze = []
    for e in ESULTANZE:
        foto, credito = foto_wikipedia(e["wiki"])
        esultanze.append({**{k: v for k, v in e.items() if k != "wiki"}, "foto": foto, "credito": credito})

    dati = {
        "aggiornato": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "stagione": stagione,
        "partite": partite,
        "classifica": classifica,
        "stemmi": stemmi,
        "esultanze": esultanze,
    }

    crea_icone()
    modello = (QUI / "modello.html").read_text(encoding="utf-8")
    js = json.dumps(dati, ensure_ascii=False).replace("</", "<\\/")
    (QUI / "index.html").write_text(modello.replace("/*__DATI__*/null", js), encoding="utf-8")
    print(f"Fatto! {len(giocate)} partite giocate, {len(classifica)} squadre, {len(esultanze)} esultanze.")
    print(f"Apri: {QUI / 'index.html'}")


if __name__ == "__main__":
    main()

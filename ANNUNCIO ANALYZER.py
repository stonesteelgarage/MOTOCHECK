import re
import json
import html
from urllib.parse import urlparse

import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI


# ============================================================
# CONFIG
# Compatibile sia con Streamlit Cloud/secrets sia con config.py locale
# ============================================================

def get_secret(nome, default=""):
    try:
        valore = st.secrets.get(nome, None)
        if valore:
            return valore
    except Exception:
        pass

    try:
        import config
        return getattr(config, nome, default)
    except Exception:
        return default


OPENAI_API_KEY = get_secret("OPENAI_API_KEY", "")
LOGO_PATH = get_secret("LOGO_PATH", "stonesteel_logo.png")


st.set_page_config(
    page_title="StoneSteel Analisi Annuncio",
    page_icon="🏍️",
    layout="centered"
)


st.markdown("""
<style>
.stApp {
    background-color: #000000;
    color: white;
}
h1, h2, h3, h4, p, label, span, div {
    color: white !important;
}
textarea, input {
    background-color: #111111 !important;
    color: white !important;
}
.stTextArea textarea {
    background-color: #111111 !important;
    color: white !important;
}
.stButton > button {
    background-color: #f5c400;
    color: black !important;
    font-weight: bold;
    border-radius: 10px;
    padding: 0.7rem 1.2rem;
    border: none;
}
.stButton > button:hover {
    background-color: #ffd700;
    color: black !important;
}
.result-box {
    background-color: #111111;
    border: 1px solid #333333;
    border-radius: 14px;
    padding: 24px;
    margin-top: 20px;
    color: white;
    line-height: 1.6;
}
.info-box {
    background-color: #1a1a1a;
    border-left: 5px solid #f5c400;
    padding: 16px;
    border-radius: 10px;
    margin-top: 18px;
    margin-bottom: 18px;
}
.debug-box {
    background-color: #111111;
    border: 1px solid #444444;
    border-radius: 10px;
    padding: 12px;
    font-size: 13px;
    color: #cccccc !important;
}
a.yellow-link {
    display: inline-block;
    background-color: #f5c400;
    color: #000000 !important;
    font-weight: bold;
    padding: 10px 16px;
    border-radius: 10px;
    text-decoration: none !important;
    margin: 8px 0 18px 0;
}
</style>
""", unsafe_allow_html=True)


try:
    st.image(LOGO_PATH, width=170)
except Exception:
    pass


st.title("StoneSteel Analisi Annuncio")

st.write(
    "Incolla il link di un annuncio moto. StoneSteel proverà a leggerlo automaticamente "
    "e produrrà un'analisi d'acquisto completa."
)


st.markdown("""
<div class="info-box">
<b>Nota importante su Subito</b><br>
Subito può bloccare la lettura automatica con sistemi anti-bot, cookie wall o contenuti caricati via JavaScript.
Questa versione prova una lettura più spinta: meta tag, dati strutturati JSON-LD, dati Next.js e testo HTML.
Se Subito blocca comunque la pagina, incolla anche il testo dell'annuncio nel box manuale.
</div>
""", unsafe_allow_html=True)


# ============================================================
# UTILITY SCRAPING SPINTO
# ============================================================

def pulisci_testo(testo):
    testo = html.unescape(str(testo or ""))
    testo = testo.replace("\xa0", " ")
    testo = re.sub(r"[ \t]+", " ", testo)
    testo = re.sub(r"\n{3,}", "\n\n", testo)
    return testo.strip()


def flatten_json(obj, prefix=""):
    righe = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            nuovo_prefix = f"{prefix}.{k}" if prefix else str(k)
            righe.extend(flatten_json(v, nuovo_prefix))

    elif isinstance(obj, list):
        for i, v in enumerate(obj[:80]):
            nuovo_prefix = f"{prefix}[{i}]"
            righe.extend(flatten_json(v, nuovo_prefix))

    else:
        valore = str(obj).strip()
        if valore and valore.lower() not in ["none", "null", "false"]:
            if len(valore) <= 1000:
                righe.append(f"{prefix}: {valore}")

    return righe


def estrai_da_meta(soup):
    campi = []

    selettori = [
        ("title", None),
        ("meta", {"property": "og:title"}),
        ("meta", {"property": "og:description"}),
        ("meta", {"property": "og:url"}),
        ("meta", {"property": "product:price:amount"}),
        ("meta", {"property": "product:price:currency"}),
        ("meta", {"name": "description"}),
        ("meta", {"name": "keywords"}),
        ("meta", {"itemprop": "name"}),
        ("meta", {"itemprop": "description"}),
        ("meta", {"itemprop": "price"}),
    ]

    for tag_name, attrs in selettori:
        if tag_name == "title":
            if soup.title and soup.title.string:
                campi.append("title: " + soup.title.string.strip())
            continue

        tag = soup.find(tag_name, attrs=attrs)
        if tag:
            contenuto = tag.get("content") or tag.get_text(" ", strip=True)
            if contenuto:
                campi.append(f"{attrs}: {contenuto}")

    return "\n".join(campi)


def estrai_json_ld(soup):
    blocchi = []
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})

    for script in scripts:
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
            righe = flatten_json(data)
            if righe:
                blocchi.append("JSON-LD:\n" + "\n".join(righe[:250]))
        except Exception:
            blocchi.append("JSON-LD RAW:\n" + raw[:4000])

    return "\n\n".join(blocchi)


def estrai_next_data(soup):
    script = soup.find("script", id="__NEXT_DATA__")
    if not script:
        return ""

    raw = script.string or script.get_text() or ""
    raw = raw.strip()
    if not raw:
        return ""

    try:
        data = json.loads(raw)
        righe = flatten_json(data)

        parole_utili = [
            "title", "subject", "description", "body", "price", "amount",
            "mileage", "km", "year", "vehicle", "brand", "model",
            "city", "town", "region", "seller", "phone", "ad", "item",
            "category", "features", "parameters"
        ]

        filtrate = []
        for riga in righe:
            low = riga.lower()
            if any(p in low for p in parole_utili):
                filtrate.append(riga)

        if filtrate:
            return "DATI NEXT/APP:\n" + "\n".join(filtrate[:350])

        return "DATI NEXT/APP:\n" + "\n".join(righe[:250])

    except Exception:
        return "DATI NEXT RAW:\n" + raw[:8000]


def estrai_testo_visibile(soup):
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    testo = soup.get_text(separator="\n")
    righe = []
    viste = set()

    for riga in testo.splitlines():
        riga = pulisci_testo(riga)
        if len(riga) < 2:
            continue
        if riga in viste:
            continue
        viste.add(riga)
        righe.append(riga)

    return "\n".join(righe[:800])


def sembra_blocco_anti_bot(status_code, testo_html, testo_estratto):
    low = (testo_html[:5000] + "\n" + testo_estratto[:5000]).lower()
    segnali = [
        "access denied", "forbidden", "captcha", "robot", "cloudflare",
        "enable javascript", "abilita javascript", "cookie", "consent",
        "non sei autorizzato", "too many requests", "unusual traffic"
    ]
    if status_code in [401, 403, 406, 429]:
        return True
    if any(s in low for s in segnali) and len(testo_estratto) < 2500:
        return True
    return False


def estrai_testo_annuncio(url):
    if not url.strip():
        return ""

    session = requests.Session()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/",
    }

    try:
        response = session.get(
            url,
            headers=headers,
            timeout=25,
            allow_redirects=True
        )

        final_url = response.url
        status_code = response.status_code
        html_text = response.text or ""

        if status_code != 200:
            return (
                f"LINK ANALIZZATO:\n{url}\n\n"
                f"URL FINALE:\n{final_url}\n\n"
                f"Pagina non leggibile direttamente. Codice errore: {status_code}.\n"
                "Probabile blocco del sito, protezione anti-bot, cookie wall o pagina non pubblica.\n"
                "Incollare le informazioni manuali dell'annuncio nel secondo box."
            )

        soup = BeautifulSoup(html_text, "html.parser")

        meta = estrai_da_meta(soup)
        json_ld = estrai_json_ld(soup)
        next_data = estrai_next_data(soup)
        testo_visibile = estrai_testo_visibile(soup)

        dominio = urlparse(final_url).netloc

        blocchi = [
            f"LINK ANALIZZATO:\n{url}",
            f"URL FINALE:\n{final_url}",
            f"DOMINIO:\n{dominio}",
            f"STATUS HTTP:\n{status_code}",
        ]

        if meta:
            blocchi.append("META TAG / OPEN GRAPH:\n" + meta)
        if json_ld:
            blocchi.append(json_ld)
        if next_data:
            blocchi.append(next_data)
        if testo_visibile:
            blocchi.append("TESTO VISIBILE PAGINA:\n" + testo_visibile)

        risultato = pulisci_testo("\n\n".join(blocchi))

        if sembra_blocco_anti_bot(status_code, html_text, risultato):
            risultato += (
                "\n\nATTENZIONE LETTURA:\n"
                "Il sito sembra aver restituito contenuto parziale o una pagina di protezione. "
                "Per Subito è normale: l'annuncio può essere caricato via JavaScript o protetto. "
                "Usare anche il box manuale per una valutazione completa."
            )

        return risultato[:30000]

    except Exception as e:
        return (
            f"LINK ANALIZZATO:\n{url}\n\n"
            f"Errore lettura annuncio: {str(e)}.\n"
            "Probabile blocco del sito o problema di rete. Usare le informazioni manuali inserite dall'utente."
        )


# ============================================================
# OPENAI ANALISI
# ============================================================

def analizza_annuncio_con_ai(url, testo_annuncio, info_manuali):
    if not OPENAI_API_KEY:
        return "Errore: manca OPENAI_API_KEY nei Secrets di Streamlit o in config.py."

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Sei StoneSteel Garage, consulente esperto di moto usate.

L'utente ha inserito questo link annuncio:
{url}

Testo letto automaticamente dall'annuncio:
{testo_annuncio}

Informazioni manuali inserite dall'utente:
{info_manuali}

Devi produrre un'analisi professionale in italiano.

Regole fondamentali:
- Riporta sempre il link dell'annuncio nella prima parte del report.
- Se il testo automatico contiene meta tag, JSON-LD, dati Next.js o dati strutturati, usali per identificare marca, modello, anno, km, prezzo, città e descrizione.
- Se il link non è leggibile ma l'utente ha inserito informazioni manuali, usa quelle informazioni come base principale.
- Non dire che l'analisi è generica se sono presenti marca, modello, anno, prezzo, km e descrizione.
- Se mancano dati importanti, evidenzialo chiaramente.
- Non inventare dati certi non presenti.
- Puoi però fare valutazioni tecniche prudenti basate su modello, categoria e anno.
- Non usare markdown complesso.
- Non usare ###.
- Non usare simboli strani.
- Scrivi in modo concreto, professionale e leggibile.

Struttura obbligatoria del report:

0. Link annuncio analizzato
Riporta il link originale incollato dall'utente.

1. Sintesi StoneSteel dell'annuncio
Spiega che moto è, che tipo di acquisto rappresenta e per quale motociclista può essere adatta.

2. Dati letti dall'annuncio
Elenca solo i dati effettivamente letti o inseriti manualmente:
- marca/modello
- anno
- chilometri
- prezzo
- città/zona
- venditore privato/concessionario se presente
- descrizione rilevante

3. Qualità dell'annuncio
Valuta se l'annuncio è completo, povero di informazioni, credibile, interessante o da approfondire.

4. Prima impressione sul prezzo
Valuta se il prezzo sembra:
- interessante
- corretto
- alto
- da trattare
- non valutabile per mancanza dati

5. Punti positivi evidenti
Elenca i punti favorevoli emersi.

6. Punti critici dell'annuncio
Indica cosa non convince:
- dati mancanti
- foto mancanti
- prezzo poco chiaro
- tagliandi non dichiarati
- chilometraggio da verificare
- accessori non omologati
- descrizione troppo povera

7. Difetti e rischi possibili del modello
Indica le fragilità tipiche del modello o della categoria.
Se il modello non è identificato con certezza, ragiona per categoria.

8. Checklist prima dell'acquisto
Scrivi almeno 18 controlli pratici:
- libretto
- targa
- telaio
- proprietari
- tagliandi
- gomme
- freni
- sospensioni
- trasmissione
- frizione
- motore
- perdite olio
- elettronica
- batteria
- scarichi
- accessori
- omologazioni
- prova su strada

9. Domande da fare al venditore
Scrivi almeno 12 domande concrete.

10. Valutazione rischio StoneSteel
Scegli uno:
- Basso
- Medio
- Alto

Spiega bene il motivo.

11. Opinione finale StoneSteel
Dai un parere netto:
- da vedere subito
- interessante ma da trattare
- da verificare con attenzione
- meglio lasciar perdere

12. Tre modelli alternativi
Suggerisci tre modelli alternativi coerenti.
Per ciascuno indica:
- perché sceglierlo
- pro
- contro
- per chi è più adatto
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Sei un consulente motociclistico esperto di moto usate e valutazioni d'acquisto."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.35
    )

    return response.choices[0].message.content


# ============================================================
# UI
# ============================================================

link_annuncio = st.text_area(
    "Incolla qui il link all'annuncio",
    height=80,
    placeholder="https://www.subito.it/moto-e-scooter/..."
)


info_manuali = st.text_area(
    "Se il link non viene letto, incolla qui testo annuncio o caratteristiche moto",
    height=220,
    placeholder=(
        "Esempio:\n"
        "Harley-Davidson Road Glide 114\n"
        "Anno 2021\n"
        "Km 18.000\n"
        "Prezzo 25.900 euro\n"
        "Città Cuneo\n"
        "Tagliandi Harley ufficiali\n"
        "Scarichi omologati\n"
        "Unico proprietario\n"
        "Descrizione del venditore..."
    )
)

mostra_debug = st.checkbox("Mostra testo tecnico letto dalla pagina", value=False)


if st.button("Analizza annuncio con StoneSteel"):
    if not link_annuncio.strip() and not info_manuali.strip():
        st.warning("Inserisci almeno il link dell'annuncio oppure le informazioni manuali della moto.")
    else:
        with st.spinner("StoneSteel sta leggendo l'annuncio..."):
            testo = estrai_testo_annuncio(link_annuncio.strip())

        if link_annuncio.strip():
            st.markdown(
                f'<a class="yellow-link" href="{link_annuncio.strip()}" target="_blank">Apri link annuncio originale</a>',
                unsafe_allow_html=True
            )

        if mostra_debug:
            st.markdown("<div class='debug-box'>", unsafe_allow_html=True)
            st.text(testo[:12000])
            st.markdown("</div>", unsafe_allow_html=True)

        with st.spinner("StoneSteel sta analizzando l'annuncio..."):
            report = analizza_annuncio_con_ai(
                link_annuncio.strip(),
                testo,
                info_manuali.strip()
            )

        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.subheader("Analisi StoneSteel")
        st.write(report)
        st.markdown("</div>", unsafe_allow_html=True)

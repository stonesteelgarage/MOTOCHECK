import re
import json
import html
import requests
import streamlit as st
from openai import OpenAI
from urllib.parse import urlparse

# ============================================================
# CONFIG
# ============================================================

try:
    from codici import (
        SERPAPI_API_KEY,
        OPENAI_API_KEY
    )

except Exception:

    SERPAPI_API_KEY = st.secrets.get(
        "SERPAPI_API_KEY",
        ""
    )

    OPENAI_API_KEY = st.secrets.get(
        "OPENAI_API_KEY",
        ""
    )

# ============================================================
# STREAMLIT
# ============================================================

st.set_page_config(
    page_title="StoneSteel Annunci Moto",
    layout="centered"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #000000;
}

h1, h2, h3, h4, h5, h6,
p, div, span, label {
    color: white !important;
}

.stTextInput input {

    background-color: #111111 !important;

    color: white !important;

    border: 1px solid #555555 !important;

    border-radius: 8px !important;
}

.stButton button {

    background-color: #f0c040 !important;

    color: black !important;

    font-weight: bold !important;

    border-radius: 8px !important;

    border: none !important;
}

.stButton button * {
    color: black !important;
}

.card {

    background-color: #111111;

    border: 1px solid #333333;

    border-radius: 12px;

    padding: 18px;

    margin-bottom: 20px;
}

.card h3 {
    color: white !important;
}

.card p {
    color: #cccccc !important;
}

.yellow-button {

    display: inline-block;

    background-color: #f0c040;

    color: black !important;

    padding: 12px 20px;

    border-radius: 10px;

    text-decoration: none !important;

    font-weight: bold;

    margin-top: 10px;

    margin-bottom: 10px;
}

.link-annuncio {

    color: #f0c040 !important;

    word-break: break-all;

    font-size: 0.92rem;
}

.info-box {

    background-color: #0b0b0b;

    border: 1px solid #333333;

    border-radius: 10px;

    padding: 12px;

    margin-top: 10px;
}

hr {
    border-color: #333333 !important;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# UTILITY
# ============================================================

def pulisci(testo):

    return re.sub(
        r"\s+",
        " ",
        str(testo).strip()
    )


def dominio_da_link(link):

    try:
        return urlparse(link).netloc.replace(
            "www.",
            ""
        )
    except Exception:
        return ""


def taglia_testo(testo, limite=12000):

    testo = pulisci(testo)

    if len(testo) <= limite:
        return testo

    return testo[:limite]


def estrai_json_da_testo(testo):

    try:
        return json.loads(testo)
    except Exception:
        pass

    match = re.search(
        r"\{.*\}",
        testo,
        re.DOTALL
    )

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return {}

    return {}

# ============================================================
# SCRAPING PAGINA ANNUNCIO
# ============================================================

def scarica_pagina_annuncio(link):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    try:
        response = requests.get(
            link,
            headers=headers,
            timeout=25,
            allow_redirects=True
        )

        if response.status_code >= 400:
            return ""

        testo_html = response.text

        # Rimuove blocchi inutili e pesanti.
        testo_html = re.sub(
            r"<script[\s\S]*?</script>",
            " ",
            testo_html,
            flags=re.IGNORECASE
        )

        testo_html = re.sub(
            r"<style[\s\S]*?</style>",
            " ",
            testo_html,
            flags=re.IGNORECASE
        )

        # Tiene anche JSON-LD e meta description perché spesso contengono prezzo,
        # località, chilometri e descrizione dell'annuncio.
        blocchi_json_ld = re.findall(
            r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>([\s\S]*?)</script>",
            response.text,
            flags=re.IGNORECASE
        )

        meta = re.findall(
            r"<meta[^>]+(?:name|property)=[\"'](?:description|og:description|og:title|title)[\"'][^>]+content=[\"']([^\"']+)[\"'][^>]*>",
            response.text,
            flags=re.IGNORECASE
        )

        testo_visibile = re.sub(
            r"<[^>]+>",
            " ",
            testo_html
        )

        testo_completo = " ".join(
            blocchi_json_ld + meta + [testo_visibile]
        )

        testo_completo = html.unescape(
            testo_completo
        )

        testo_completo = pulisci(
            testo_completo
        )

        return taglia_testo(
            testo_completo,
            14000
        )

    except Exception:
        return ""

# ============================================================
# OPENAI ESTRAZIONE DATI ANNUNCIO
# ============================================================

def analizza_annuncio_con_openai(
    marca,
    modello,
    annuncio
):

    if not OPENAI_API_KEY:

        raise ValueError(
            "OPENAI_API_KEY mancante."
        )

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    prompt = f"""
Sei StoneSteel Garage, esperto di moto usate.

Devi leggere in modo aggressivo i dati disponibili di un annuncio moto.
Usa titolo, snippet Google, link e testo scaricato dalla pagina.

NON inventare dati.
Se un dato non è presente scrivi "N.D.".
Il link deve essere sempre restituito identico.

Moto cercata:
{marca} {modello}

Annuncio grezzo:
{json.dumps(annuncio, ensure_ascii=False, indent=2)}

Estrai e valuta:
- titolo pulito
- link annuncio
- sito/dominio
- prezzo
- anno
- chilometri
- località
- venditore, se disponibile
- descrizione sintetica reale
- punti interessanti
- rischi o punti da controllare
- punteggio StoneSteel da 1 a 10
- giudizio prezzo: basso, corretto, alto, non valutabile
- valutazione StoneSteel concreta

Rispondi SOLO in JSON valido.
Formato esatto:

{{
  "titolo": "...",
  "link": "...",
  "sito": "...",
  "prezzo": "...",
  "anno": "...",
  "chilometri": "...",
  "localita": "...",
  "venditore": "...",
  "descrizione": "...",
  "punti_interessanti": "...",
  "controlli": "...",
  "punteggio": "8",
  "giudizio_prezzo": "corretto",
  "valutazione": "..."
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Rispondi solo in JSON valido. Non inventare dati."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    testo = (
        response
        .choices[0]
        .message.content
    )

    data = estrai_json_da_testo(
        testo
    )

    if not data:
        data = {}

    data["link"] = annuncio.get(
        "link",
        ""
    )

    if not data.get("sito"):
        data["sito"] = dominio_da_link(
            annuncio.get("link", "")
        )

    return data

# ============================================================
# CERCA ANNUNCI VERI
# ============================================================

def cerca_annunci_veri(
    marca,
    modello
):

    if not SERPAPI_API_KEY:

        raise ValueError(
            "SERPAPI_API_KEY mancante."
        )

    query_principale = (
        f"{marca} {modello} "
        "moto usata "
        "Subito Moto.it AutoScout24"
    )

    query_secondarie = [
        query_principale,
        f'site:subito.it {marca} {modello} moto usata',
        f'site:moto.it {marca} {modello} usata',
        f'site:autoscout24.it {marca} {modello} moto usata',
    ]

    url = (
        "https://serpapi.com/search.json"
    )

    risultati = []
    link_visti = set()

    domini_validi = [

        "subito.it",

        "moto.it",

        "autoscout24.it",

        "facebook.com/marketplace"
    ]

    for query in query_secondarie:

        params = {

            "engine": "google",

            "q": query,

            "hl": "it",

            "gl": "it",

            "num": 20,

            "api_key": SERPAPI_API_KEY
        }

        response = requests.get(
            url,
            params=params,
            timeout=60
        )

        if response.status_code != 200:

            raise ValueError(
                f"Errore SerpAPI "
                f"{response.status_code}: "
                f"{response.text}"
            )

        data = response.json()

        for item in data.get(
            "organic_results",
            []
        ):

            titolo = item.get(
                "title",
                ""
            )

            link = item.get(
                "link",
                ""
            )

            snippet = item.get(
                "snippet",
                ""
            )

            if not link:
                continue

            if link in link_visti:
                continue

            if not any(
                dominio in link
                for dominio in domini_validi
            ):
                continue

            link_visti.add(
                link
            )

            risultati.append({

                "titolo": pulisci(titolo),

                "link": link,

                "descrizione": pulisci(snippet),

                "sito": dominio_da_link(link)
            })

            if len(risultati) >= 10:
                break

        if len(risultati) >= 10:
            break

    return risultati

# ============================================================
# SCRAPING SPINTO + VALUTAZIONE STONESTEEL
# ============================================================

def valuta_annunci(
    marca,
    modello,
    annunci
):

    valutazioni = []

    for annuncio in annunci:

        testo_pagina = scarica_pagina_annuncio(
            annuncio.get("link", "")
        )

        annuncio_arricchito = dict(
            annuncio
        )

        annuncio_arricchito["testo_pagina_scrapato"] = testo_pagina

        try:
            valutazione = analizza_annuncio_con_openai(
                marca,
                modello,
                annuncio_arricchito
            )
        except Exception:
            valutazione = {}

        if not valutazione:
            valutazione = {
                "titolo": annuncio.get("titolo", "N.D."),
                "link": annuncio.get("link", ""),
                "sito": annuncio.get("sito", "N.D."),
                "prezzo": "N.D.",
                "anno": "N.D.",
                "chilometri": "N.D.",
                "localita": "N.D.",
                "venditore": "N.D.",
                "descrizione": annuncio.get("descrizione", "N.D."),
                "punti_interessanti": "N.D.",
                "controlli": "N.D.",
                "punteggio": "N.D.",
                "giudizio_prezzo": "non valutabile",
                "valutazione": "Dati insufficienti: aprire il link e verificare manualmente."
            }

        valutazione["link"] = annuncio.get(
            "link",
            ""
        )

        valutazione["titolo_originale"] = annuncio.get(
            "titolo",
            ""
        )

        valutazione["descrizione_originale"] = annuncio.get(
            "descrizione",
            ""
        )

        valutazioni.append(
            valutazione
        )

    return valutazioni

# ============================================================
# UI
# ============================================================

st.title(
    "StoneSteel Annunci Moto"
)

st.subheader(
    "10 annunci veri + scraping OpenAI + valutazione StoneSteel"
)

st.write(
    "Inserisci marca e modello."
)

marca = st.text_input(
    "Marca"
)

modello = st.text_input(
    "Modello"
)

# ============================================================
# AVVIO
# ============================================================

if st.button(
    "Cerca 10 annunci veri"
):

    if not marca or not modello:

        st.error(
            "Inserisci marca e modello."
        )

    else:

        try:

            with st.spinner(
                "Ricerca annunci online..."
            ):

                annunci = (
                    cerca_annunci_veri(
                        marca,
                        modello
                    )
                )

            if not annunci:

                st.warning(
                    "Nessun annuncio trovato."
                )

            else:

                with st.spinner(
                    "StoneSteel sta facendo scraping e analisi AI degli annunci..."
                ):

                    valutazioni = (
                        valuta_annunci(
                            marca,
                            modello,
                            annunci
                        )
                    )

                st.success(
                    "Annunci trovati e analizzati."
                )

                for i, annuncio in enumerate(
                    annunci,
                    start=1
                ):

                    valutazione = {}

                    if (
                        i - 1
                        < len(valutazioni)
                    ):

                        valutazione = (
                            valutazioni[i - 1]
                        )

                    titolo_finale = valutazione.get(
                        "titolo",
                        annuncio.get("titolo", "N.D.")
                    )

                    link_finale = valutazione.get(
                        "link",
                        annuncio.get("link", "")
                    )

                    descrizione_finale = valutazione.get(
                        "descrizione",
                        annuncio.get("descrizione", "N.D.")
                    )

                    st.markdown(
                        f"""
                        <div class="card">

                        <h3>
                        {i}. {html.escape(str(titolo_finale))}
                        </h3>

                        <p>
                        {html.escape(str(descrizione_finale))}
                        </p>

                        <p class="link-annuncio">
                        Link annuncio: {html.escape(str(link_finale))}
                        </p>

                        <a class="yellow-button"
                           href="{html.escape(str(link_finale))}"
                           target="_blank">
                           Apri annuncio reale
                        </a>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f"""
                        <div class="info-box">
                        <p><b>Sito:</b> {html.escape(str(valutazione.get('sito', annuncio.get('sito', 'N.D.'))))}</p>
                        <p><b>Prezzo:</b> {html.escape(str(valutazione.get('prezzo', 'N.D.')))}</p>
                        <p><b>Anno:</b> {html.escape(str(valutazione.get('anno', 'N.D.')))}</p>
                        <p><b>Km:</b> {html.escape(str(valutazione.get('chilometri', 'N.D.')))}</p>
                        <p><b>Località:</b> {html.escape(str(valutazione.get('localita', 'N.D.')))}</p>
                        <p><b>Venditore:</b> {html.escape(str(valutazione.get('venditore', 'N.D.')))}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.write(
                        f"⭐ Punteggio StoneSteel: "
                        f"{valutazione.get('punteggio', 'N.D.')}/10"
                    )

                    st.write(
                        f"🛠 Valutazione: "
                        f"{valutazione.get('valutazione', 'N.D.')}"
                    )

                    st.write(
                        f"✅ Punti interessanti: "
                        f"{valutazione.get('punti_interessanti', 'N.D.')}"
                    )

                    st.write(
                        f"🔍 Controlli: "
                        f"{valutazione.get('controlli', 'N.D.')}"
                    )

                    st.write(
                        f"💰 Prezzo: "
                        f"{valutazione.get('giudizio_prezzo', 'N.D.')}"
                    )

                    st.markdown("---")

        except Exception as e:

            st.error(
                f"Errore: {e}"
            )

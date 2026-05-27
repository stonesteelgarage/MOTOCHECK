import re
import json
import requests
import streamlit as st
from openai import OpenAI

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

hr {
    border-color: #333333 !important;
}

.card {

    background-color: #111111;

    border: 1px solid #333333;

    border-radius: 12px;

    padding: 16px;

    margin-bottom: 18px;
}

.card h3 {
    color: white !important;
}

.card p {
    color: #cccccc !important;
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

    query = (
        f"{marca} {modello} "
        "moto usata "
        "Subito Moto.it AutoScout24"
    )

    url = (
        "https://serpapi.com/search.json"
    )

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

    risultati = []

    domini_validi = [

        "subito.it",

        "moto.it",

        "autoscout24.it",

        "facebook.com/marketplace"
    ]

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

        if not any(
            dominio in link
            for dominio in domini_validi
        ):
            continue

        risultati.append({

            "titolo": titolo,

            "link": link,

            "descrizione": snippet
        })

        if len(risultati) >= 10:
            break

    return risultati

# ============================================================
# VALUTAZIONE STONESTEEL
# ============================================================

def valuta_annunci(
    marca,
    modello,
    annunci
):

    if not OPENAI_API_KEY:

        raise ValueError(
            "OPENAI_API_KEY mancante."
        )

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    prompt = f"""
Sei StoneSteel Garage,
esperto di moto usate.

Valuta questi annunci.

Marca:
{marca}

Modello:
{modello}

Annunci:
{json.dumps(annunci, ensure_ascii=False, indent=2)}

Per ogni annuncio restituisci:
- punteggio da 1 a 10
- valutazione breve
- cosa controllare
- se il prezzo sembra alto, basso o corretto

NON inventare dati.

Rispondi SOLO in JSON valido.

Formato:

{{
  "valutazioni": [
    {{
      "punteggio": "8",
      "valutazione": "...",
      "controlli": "...",
      "prezzo": "corretto"
    }}
  ]
}}
"""

    response = client.chat.completions.create(

        model="gpt-4.1-mini",

        messages=[

            {
                "role": "system",
                "content":
                "Rispondi solo in JSON valido."
            },

            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.3
    )

    testo = (
        response
        .choices[0]
        .message.content
    )

    try:

        data = json.loads(testo)

        return data.get(
            "valutazioni",
            []
        )

    except Exception:

        return []

# ============================================================
# UI
# ============================================================

st.title(
    "StoneSteel Annunci Moto"
)

st.subheader(
    "10 annunci veri + valutazione StoneSteel"
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
                    "StoneSteel sta valutando..."
                ):

                    valutazioni = (
                        valuta_annunci(
                            marca,
                            modello,
                            annunci
                        )
                    )

                st.success(
                    "Annunci trovati."
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

                    st.markdown(
                        f"""
                        <div class="card">

                        <h3>
                        {i}. {annuncio["titolo"]}
                        </h3>

                        <p>
                        {annuncio["descrizione"]}
                        </p>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.link_button(
                        "Apri annuncio reale",
                        annuncio["link"]
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
                        f"🔍 Controlli: "
                        f"{valutazione.get('controlli', 'N.D.')}"
                    )

                    st.write(
                        f"💰 Prezzo: "
                        f"{valutazione.get('prezzo', 'N.D.')}"
                    )

                    st.markdown("---")

        except Exception as e:

            st.error(
                f"Errore: {e}"
            )

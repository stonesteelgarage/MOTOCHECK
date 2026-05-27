```python
import streamlit as st
from openai import OpenAI
import os
import re
from urllib.parse import quote

# =========================
# CONFIG / STREAMLIT SECRETS
# =========================

try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    from config import OPENAI_API_KEY

try:
    LOGO_PATH = st.secrets["LOGO_PATH"]
except Exception:
    try:
        from config import LOGO_PATH
    except Exception:
        LOGO_PATH = "stonesteel_logo.png"

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# PAGINA
# =========================

st.set_page_config(
    page_title="StoneSteel Cerca Annunci",
    page_icon="🏍️",
    layout="centered"
)

# =========================
# STILE
# =========================

st.markdown("""
<style>

.stApp {
    background-color: #050505;
    color: white;
}

h1, h2, h3, h4, h5, h6,
p, div, span, label, li {
    color: white !important;
}

a {
    color: #f2c94c !important;
    font-weight: bold;
}

.stTextInput input {
    background-color: #111111;
    color: white !important;
    border: 1px solid #444444;
    border-radius: 8px;
}

.stButton button {
    background-color: #f2c94c;
    color: black !important;
    font-weight: bold;
    border-radius: 10px;
    border: none;
    padding: 0.7rem 1.2rem;
}

.report-box {
    background-color: #111111;
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #333333;
    margin-top: 20px;
    line-height: 1.8;
    color: white !important;
    word-wrap: break-word;
    overflow-wrap: break-word;
}

.report-box * {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# PULIZIA TESTO
# =========================

def pulisci_testo(testo):

    if not testo:
        return ""

    sostituzioni = {
        "€": "EUR",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "’": "'",
        "‘": "'",
        "•": "-",
        "…": "...",
    }

    for vecchio, nuovo in sostituzioni.items():
        testo = testo.replace(vecchio, nuovo)

    return testo

# =========================
# LINK SUBITO RICERCA
# =========================

def genera_link_subito(marca, modello):

    query = quote(f"{marca} {modello}")

    return (
        "https://www.subito.it/annunci-italia/"
        f"vendita/moto-e-scooter/?q={query}"
    )

# =========================
# AI ANNUNCI
# =========================

def genera_analisi_annunci(marca, modello):

    link_subito = genera_link_subito(marca, modello)

    prompt = f"""
Sei StoneSteel Garage.

Sei un advisor motociclistico italiano esperto.

Devi cercare online annunci REALI in Italia per:

Marca: {marca}
Modello: {modello}

Cerca soprattutto su:
- moto.it
- autoscout24.it
- concessionari italiani
- subito.it SOLO se il link è chiaramente valido

Obiettivo:
trovare fino a 10 annunci reali.

Formato risposta:

### ANNUNCIO 1

Titolo:
Prezzo:
Localita:
Link:
Riassunto:
Valutazione prezzo:
Parere StoneSteel:
Controlli consigliati:

Regole IMPORTANTI:
- NON inventare annunci.
- NON inventare URL.
- NON usare link Subito diretti se non sei sicuro siano funzionanti.
- Se un link Subito non è verificabile, evita di inserirlo.
- Preferisci Moto.it, AutoScout24 e concessionari.
- Scrivi in italiano.
- Usa markdown semplice.
- Non usare tabelle.
- Non usare simboli strani.
- Alla fine fai una sintesi del mercato italiano per questo modello.

Alla fine aggiungi anche:

### RICERCA SUBITO.IT

Link ricerca generale:
{link_subito}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        tools=[{"type": "web_search"}],
        input=prompt
    )

    return response.output_text

# =========================
# INTERFACCIA
# =========================

if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=170)

st.title("StoneSteel Cerca Annunci")

st.write(
    "Trova annunci moto in Italia e ricevi una prima valutazione StoneSteel."
)

marca = st.text_input(
    "Marca moto",
    placeholder="Esempio: Harley-Davidson"
)

modello = st.text_input(
    "Modello moto",
    placeholder="Esempio: Road King"
)

# =========================
# BOTTONE
# =========================

if st.button("Cerca annunci in Italia"):

    if not marca or not modello:

        st.error("Inserisci marca e modello.")

    else:

        with st.spinner("🏍️ StoneSteel sta cercando gli annunci migliori..."):

            try:

                report = genera_analisi_annunci(
                    marca,
                    modello
                )

                report = pulisci_testo(report)

                st.markdown(
                    "<div class='report-box'>",
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"<div style='color:white'>{report}</div>",
                    unsafe_allow_html=True
                )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )

            except Exception as e:

                st.error(f"Errore durante la ricerca: {e}")
```

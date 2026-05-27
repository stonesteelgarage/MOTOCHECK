import streamlit as st
from openai import OpenAI
import os
import re

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

h1, h2, h3, p, div, label {
    color: white;
}

a {
    color: #f2c94c !important;
    font-weight: bold;
}

.stTextInput input {
    background-color: #111111;
    color: white;
    border: 1px solid #444444;
    border-radius: 8px;
}

.stButton button {
    background-color: #f2c94c;
    color: black;
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
    line-height: 1.7;
    word-wrap: break-word;
    overflow-wrap: break-word;
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
# AI ANNUNCI
# =========================

def genera_analisi_annunci(marca, modello):

    prompt = f"""
Sei StoneSteel Garage, advisor motociclistico italiano.

Devi cercare online annunci REALI in Italia per:

Marca: {marca}
Modello: {modello}

Cerca soprattutto su:
- subito.it
- moto.it
- autoscout24.it
- concessionari italiani
- altri siti affidabili italiani

Obiettivo:
trovare fino a 10 annunci reali.

Per ogni annuncio restituisci in questo formato:

### ANNUNCIO 1
**Titolo:** ...
**Prezzo:** ...
**Località:** ...
**Link:** https://...
**Riassunto:** ...
**Valutazione prezzo:** basso / corretto / alto / sospetto
**Parere StoneSteel:** ...
**Controlli consigliati:** ...

Regole:
- Non inventare annunci.
- Non inventare link.
- Se trovi meno di 10 annunci, dichiaralo chiaramente.
- Il link deve essere completo e cliccabile.
- Scrivi in italiano.
- Usa markdown semplice.
- Non usare tabelle.
- Tono concreto e professionale.
- Alla fine fai una sintesi del mercato italiano per questo modello.
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

if st.button("Cerca annunci in Italia"):

    if not marca or not modello:
        st.error("Inserisci marca e modello.")

    else:
        with st.spinner("🏍️ StoneSteel sta cercando gli annunci migliori..."):

            try:
                report = genera_analisi_annunci(marca, modello)
                report = pulisci_testo(report)

                st.markdown(
                    "<div class='report-box'>",
                    unsafe_allow_html=True
                )

                st.markdown(report, unsafe_allow_html=True)

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )

            except Exception as e:
                st.error(f"Errore durante la ricerca: {e}")

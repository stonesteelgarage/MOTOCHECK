import streamlit as st
from openai import OpenAI
from fpdf import FPDF
import tempfile
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

.stDownloadButton button {
    background-color: #f2c94c;
    color: black;
    font-weight: bold;
    border-radius: 10px;
    border: none;
}

.report-box {
    background-color: #111111;
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #333333;
    margin-top: 20px;
    line-height: 1.7;
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

    testo = re.sub(r"[^\x00-\xFF]", "", testo)

    return testo

# =========================
# AI ANNUNCI
# =========================

def genera_analisi_annunci(marca, modello):

    prompt = f"""
Sei StoneSteel Garage.

Sei un esperto motociclistico italiano specializzato in Harley, BMW, Ducati, Honda, Yamaha, Triumph, Moto Guzzi e moto custom/touring.

Devi cercare online 10 annunci REALI in Italia per:

Marca: {marca}
Modello: {modello}

Cerca soprattutto su:
- subito.it
- moto.it
- autoscout24.it
- concessionari italiani
- altri siti affidabili italiani

Per ogni annuncio restituisci:

1. Numero annuncio
2. Titolo annuncio
3. Prezzo
4. Località
5. Link completo
6. Riassunto rapido dell'annuncio
7. Valutazione prezzo:
   - basso
   - corretto
   - alto
   - sospetto
8. Parere StoneSteel:
   se vale la pena considerarla oppure no
9. Controlli consigliati

Regole:
- Non inventare annunci.
- Non inventare link.
- Cerca annunci realmente esistenti.
- Scrivi in italiano.
- Non usare markdown.
- Non usare tabelle markdown.
- Tono professionale ma concreto.
- Alla fine fai una sintesi del mercato italiano per questo modello.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        tools=[{"type": "web_search"}],
        input=prompt
    )

    return response.output_text

# =========================
# PDF
# =========================

class PDF(FPDF):

    def header(self):

        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=10, y=8, w=32)

        self.set_y(42)

        self.set_font("Arial", "B", 15)

        self.cell(
            0,
            10,
            "StoneSteel Garage - Ricerca Annunci Moto",
            ln=True,
            align="C"
        )

        self.ln(6)

    def footer(self):

        self.set_y(-15)

        self.set_font("Arial", "", 8)

        self.cell(
            0,
            10,
            f"Pagina {self.page_no()}",
            align="C"
        )

# =========================
# CREA PDF
# =========================

def crea_pdf(marca, modello, report):

    pdf = PDF()

    pdf.set_auto_page_break(auto=True, margin=18)

    pdf.add_page()

    pdf.set_font("Arial", "B", 13)

    titolo = f"Ricerca annunci - {marca} {modello}"

    pdf.cell(0, 10, pulisci_testo(titolo), ln=True)

    pdf.ln(6)

    pdf.set_font("Arial", "", 10)

    testo = pulisci_testo(report)

    righe = testo.split("\n")

    for riga in righe:

        riga = riga.strip()

        if not riga:
            pdf.ln(3)
            continue

        if (
            "Annuncio" in riga
            or "Parere" in riga
            or "Valutazione" in riga
            or "Sintesi" in riga
        ):
            pdf.set_font("Arial", "B", 11)
            pdf.multi_cell(0, 7, riga)
            pdf.set_font("Arial", "", 10)
        else:
            pdf.multi_cell(0, 6, riga)

    temp_pdf = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    pdf.output(temp_pdf.name)

    return temp_pdf.name

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

                st.markdown(
                    "<div class='report-box'>",
                    unsafe_allow_html=True
                )

                st.markdown(
                    report.replace("\n", "<br>"),
                    unsafe_allow_html=True
                )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )

                pdf_path = crea_pdf(
                    marca,
                    modello,
                    report
                )

                with open(pdf_path, "rb") as file_pdf:

                    st.download_button(
                        label="Scarica PDF",
                        data=file_pdf,
                        file_name=f"StoneSteel_Annunci_{marca}_{modello}.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:

                st.error(f"Errore durante la ricerca: {e}")

import streamlit as st
from openai import OpenAI
from fpdf import FPDF
import tempfile
import os
import re
import textwrap

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

    testo = re.sub(r"[^\x00-\xFF]", "", testo)
    return testo


def spezza_riga_lunga(riga, lunghezza=95):
    riga = pulisci_testo(riga)
    riga = riga.encode("latin-1", "replace").decode("latin-1")

    if "http" in riga and len(riga) > 120:
        riga = riga[:120] + "..."

    return textwrap.wrap(
        riga,
        width=lunghezza,
        break_long_words=True,
        break_on_hyphens=False
    )

# =========================
# AI ANNUNCI
# =========================

def genera_analisi_annunci(marca, modello):

    prompt = f"""
Sei StoneSteel Garage.

Sei un esperto motociclistico italiano.

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

Per ogni annuncio restituisci:

ANNUNCIO 1
Titolo:
Prezzo:
Localita:
Link:
Riassunto:
Valutazione prezzo:
Parere StoneSteel:
Controlli consigliati:

Regole:
- Non inventare annunci.
- Non inventare link.
- Se trovi meno di 10 annunci, dichiaralo.
- Link completi ma non eccessivamente lunghi.
- Scrivi in italiano.
- Non usare markdown.
- Non usare tabelle.
- Non usare simboli strani.
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
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "", 8)
        self.cell(
            0,
            10,
            f"Pagina {self.page_no()}",
            align="C"
        )


def crea_pdf(marca, modello, report):

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_font("Arial", "B", 13)
    pdf.multi_cell(
        0,
        8,
        pulisci_testo(f"Ricerca annunci - {marca} {modello}")
    )
    pdf.ln(5)

    testo = pulisci_testo(report)

    for riga in testo.split("\n"):
        riga = riga.strip()

        if not riga:
            pdf.ln(3)
            continue

        is_titolo = (
            riga.upper().startswith("ANNUNCIO")
            or riga.startswith("Sintesi")
            or riga.startswith("Parere")
            or riga.startswith("Valutazione")
        )

        if is_titolo:
            pdf.set_font("Arial", "B", 11)
            altezza = 7
        else:
            pdf.set_font("Arial", "", 10)
            altezza = 6

        righe_spezzate = spezza_riga_lunga(riga)

        for pezzo in righe_spezzate:
            pdf.multi_cell(180, altezza, pezzo)

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
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

if st.button("Cerca annunci in Italia"):

    if not marca or not modello:
        st.error("Inserisci marca e modello.")

    else:
        with st.spinner("🏍️ StoneSteel sta cercando gli annunci migliori..."):

            try:
                report = genera_analisi_annunci(marca, modello)

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

                pdf_path = crea_pdf(marca, modello, report)

                with open(pdf_path, "rb") as file_pdf:
                    st.download_button(
                        label="Scarica PDF",
                        data=file_pdf,
                        file_name=f"StoneSteel_Annunci_{marca}_{modello}.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Errore durante la ricerca: {e}")
        

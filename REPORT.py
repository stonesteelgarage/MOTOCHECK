import os
import tempfile
import unicodedata
import requests

import streamlit as st
from openai import OpenAI
from fpdf import FPDF

# =========================================================
# CONFIG COMPATIBILE MAC + STREAMLIT CLOUD
# =========================================================

def leggi_secret(nome, default=""):
    try:
        return st.secrets.get(nome, default)
    except Exception:
        return default


try:
    from config import OPENAI_API_KEY, LOGO_PATH
except Exception:
    OPENAI_API_KEY = leggi_secret("OPENAI_API_KEY", "")
    LOGO_PATH = leggi_secret("LOGO_PATH", "stonesteel_logo.png")


st.set_page_config(
    page_title="StoneSteel MotoCheck",
    layout="centered"
)

# =========================================================
# STILE GRAFICO
# =========================================================

st.markdown("""
<style>
.stApp {
    background-color: #000000;
    color: white;
}

h1, h2, h3, h4, h5, h6, p, div, span, label {
    color: white !important;
}

.stTextInput input {
    background-color: #111111 !important;
    color: white !important;
    border: 1px solid #555555 !important;
    border-radius: 8px !important;
}

/* PULSANTI GIALLI CON TESTO NERO */
.stButton button,
.stDownloadButton button {
    background-color: #f0c040 !important;
    color: #000000 !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: none !important;
}

.stButton button *,
.stDownloadButton button * {
    color: #000000 !important;
}

.stButton button p,
.stDownloadButton button p {
    color: #000000 !important;
}

.stButton button span,
.stDownloadButton button span {
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.title("StoneSteel MotoCheck")
st.subheader("Report con i consigli di StoneSteel")

# =========================================================
# PULIZIA TESTO
# =========================================================

def pulisci_testo(testo):
    if testo is None:
        return ""

    testo = str(testo)

    testo = testo.replace("###", "")
    testo = testo.replace("##", "")
    testo = testo.replace("#", "")
    testo = testo.replace("**", "")
    testo = testo.replace("---", "")
    testo = testo.replace("[ ]", "-")

    sostituzioni = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "-",
        "\u20ac": "EUR",
        "\u00a0": " ",
        "\u2026": "...",
    }

    for k, v in sostituzioni.items():
        testo = testo.replace(k, v)

    testo = unicodedata.normalize("NFKD", testo)
    testo = testo.encode("latin-1", "ignore").decode("latin-1")

    return testo


def pulisci_pagine_pdf(pdf):
    for pagina in list(pdf.pages.keys()):
        pdf.pages[pagina] = pulisci_testo(pdf.pages[pagina])


# =========================================================
# FOTO MOTO
# =========================================================

def trova_foto_moto(marca, modello):
    query = f"{marca} {modello} motorcycle"

    try:
        image_url = f"https://source.unsplash.com/1200x800/?{query}"

        response = requests.get(
            image_url,
            timeout=15
        )

        if response.status_code == 200:
            temp_img = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".jpg"
            )

            temp_img.write(response.content)
            temp_img.close()

            return temp_img.name

    except Exception as e:
        print("Errore immagine:", e)

    return None


# =========================================================
# PDF
# =========================================================

class PDF(FPDF):

    def header(self):
        if os.path.exists(LOGO_PATH):
            try:
                self.image(
                    LOGO_PATH,
                    x=85,
                    y=6,
                    w=35
                )
            except Exception:
                pass

        self.ln(52)

        self.set_font(
            "Helvetica",
            "B",
            16
        )

        self.cell(
            0,
            8,
            "StoneSteel MotoCheck",
            ln=True,
            align="C"
        )

        self.set_font(
            "Helvetica",
            "",
            10
        )

        self.cell(
            0,
            6,
            "Report con i consigli di StoneSteel",
            ln=True,
            align="C"
        )

        self.ln(12)

    def footer(self):
        self.set_y(-15)

        self.set_font(
            "Helvetica",
            "I",
            8
        )

        self.cell(
            0,
            10,
            f"Pagina {self.page_no()}",
            align="C"
        )


# =========================================================
# SEZIONI PDF
# =========================================================

def pdf_sezione(pdf, titolo):
    pdf.set_font(
        "Helvetica",
        "B",
        14
    )

    pdf.set_fill_color(
        230,
        230,
        230
    )

    pdf.cell(
        0,
        9,
        pulisci_testo(titolo),
        ln=True,
        fill=True
    )

    pdf.ln(4)


def pdf_testo(pdf, contenuto):
    pdf.set_font(
        "Helvetica",
        "",
        10.5
    )

    contenuto = pulisci_testo(contenuto)

    righe = contenuto.splitlines()

    for riga in righe:
        riga = riga.strip()

        if not riga:
            pdf.ln(2)
            continue

        if riga.startswith("-"):
            pdf.set_x(18)

            pdf.multi_cell(
                0,
                6.5,
                riga
            )
        else:
            pdf.multi_cell(
                0,
                6.5,
                riga
            )

    pdf.ln(2)


# =========================================================
# TABELLA PREZZI
# =========================================================

def pdf_tabella_prezzi(pdf):
    pdf.set_font(
        "Helvetica",
        "B",
        10
    )

    pdf.set_fill_color(
        220,
        220,
        220
    )

    pdf.cell(35, 10, "Fascia", 1, 0, "C", True)
    pdf.cell(40, 10, "Prezzo minimo", 1, 0, "C", True)
    pdf.cell(40, 10, "Prezzo massimo", 1, 0, "C", True)
    pdf.cell(75, 10, "Descrizione", 1, 1, "C", True)

    pdf.set_font(
        "Helvetica",
        "",
        9
    )

    righe = [
        [
            "Basso",
            "6.000 EUR",
            "8.000 EUR",
            "Moto con km elevati o lavori"
        ],
        [
            "Medio",
            "8.000 EUR",
            "11.000 EUR",
            "Moto in buone condizioni"
        ],
        [
            "Alto",
            "11.000 EUR",
            "15.000 EUR",
            "Moto molto curata"
        ]
    ]

    for r in righe:
        pdf.cell(35, 10, r[0], 1, 0, "C")
        pdf.cell(40, 10, r[1], 1, 0, "C")
        pdf.cell(40, 10, r[2], 1, 0, "C")
        pdf.cell(75, 10, r[3], 1, 1, "L")

    pdf.ln(6)


# =========================================================
# AI
# =========================================================

def genera_report_ai(marca, modello, anno):
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY non configurata. Inseriscila nei Secrets di Streamlit Cloud."
        )

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Genera un report motociclistico professionale in italiano.

Marca: {marca}
Modello: {modello}
Anno: {anno}

NON usare markdown.
NON usare ###.
NON usare **.

Usa sezioni normali ed elenchi puntati semplici.

Il report deve includere:

1. Sintesi moto
2. Dati tecnici principali
3. Caratteristiche principali
4. Difetti ricorrenti
5. Punti di attenzione
6. Opinioni utenti
7. Checklist personalizzata
8. Analisi mercato usato
9. Valutazione degli esperti StoneSteel Garage
10. Conclusione finale

La valutazione degli esperti StoneSteel Garage deve essere lunga e concreta.
La conclusione finale deve essere molto dettagliata.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Sei un esperto motociclistico professionale."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return pulisci_testo(
        response.choices[0].message.content
    )


# =========================================================
# CREA PDF
# =========================================================

def crea_pdf(marca, modello, anno, report_ai):
    pdf = PDF()

    pdf.set_auto_page_break(
        auto=True,
        margin=16
    )

    pdf.add_page()

    foto_moto = trova_foto_moto(
        marca,
        modello
    )

    if foto_moto and os.path.exists(foto_moto):
        try:
            pdf.image(
                foto_moto,
                x=25,
                y=82,
                w=160
            )

            pdf.ln(95)
        except Exception:
            pdf.ln(10)
    else:
        pdf.ln(10)

    titolo = f"Report motociclistico completo per {marca} {modello} anno {anno}"

    pdf.set_font(
        "Helvetica",
        "B",
        16
    )

    pdf.multi_cell(
        0,
        9,
        pulisci_testo(titolo)
    )

    pdf.ln(8)

    pdf_sezione(
        pdf,
        "Analisi StoneSteel"
    )

    pdf_testo(
        pdf,
        report_ai
    )

    pdf_sezione(
        pdf,
        "Confronto prezzi medi usato"
    )

    pdf_tabella_prezzi(pdf)

    pdf_sezione(
        pdf,
        "Note e limiti"
    )

    pdf_testo(
        pdf,
        "Questo report è stato generato da un'analisi dello StoneSteel Garage."
    )

    pulisci_pagine_pdf(pdf)

    temp_pdf = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    pdf.output(temp_pdf.name)

    return temp_pdf.name


# =========================================================
# INTERFACCIA
# =========================================================

st.markdown("## Report Base")

marca = st.text_input("Marca")
modello = st.text_input("Modello")
anno = st.text_input("Anno")

if st.button("Genera Report"):
    if not marca or not modello or not anno:
        st.error(
            "Inserisci marca, modello e anno."
        )
    else:
        try:
            with st.spinner(
                "StoneSteel sta generando il report..."
            ):
                report_ai = genera_report_ai(
                    marca,
                    modello,
                    anno
                )

                pdf_path = crea_pdf(
                    marca,
                    modello,
                    anno,
                    report_ai
                )

            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Scarica PDF",
                    data=f,
                    file_name=f"StoneSteel_Report_{marca}_{modello}_{anno}.pdf",
                    mime="application/pdf"
                )

            st.success(
                "Report generato correttamente."
            )

        except Exception as e:
            st.error(f"Errore durante la generazione del report: {e}")

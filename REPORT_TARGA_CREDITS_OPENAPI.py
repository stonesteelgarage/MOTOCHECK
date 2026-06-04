import os
import re
import json
import tempfile
import unicodedata
import requests

import streamlit as st
from openai import OpenAI
from fpdf import FPDF


# ============================================================
# SECRETS STREAMLIT CLOUD
# ============================================================

def secret(nome, default=""):
    try:
        return st.secrets.get(nome, default)
    except Exception:
        return default


OPENAI_API_KEY = secret("OPENAI_API_KEY")
OPENAPI_TOKEN = secret("OPENAPI_TOKEN")

# Endpoint corretto OpenAPI Automotive Moto Italia:
# base URL + /{targa}
OPENAPI_TARGA_URL = secret("OPENAPI_TARGA_URL", "https://automotive.openapi.it/IT-bike")

# Backend StoneSteel / FastAPI credits-job system
BACKEND_URL = secret("BACKEND_URL", "http://127.0.0.1:8000")
REQUIRE_BACKEND_JOB = str(secret("REQUIRE_BACKEND_JOB", "true")).lower() in ["true", "1", "yes", "si"]

LOGO_PATH = secret("LOGO_PATH", "stonesteel_logo.png")


# ============================================================
# STREAMLIT
# ============================================================

st.set_page_config(
    page_title="StoneSteel MotoCheck",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background-color: #000000;
    color: white;
}
h1,h2,h3,h4,h5,h6,p,div,span,label {
    color: white !important;
}
.stTextInput input,
.stTextArea textarea,
.stSelectbox div {
    background-color: #111111 !important;
    color: white !important;
}
.stButton button,
.stDownloadButton button {
    background-color: #f0c040 !important;
    color: black !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: none !important;
}
.stButton button *,
.stDownloadButton button * {
    color: black !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# BACKEND CREDITS / JOB
# ============================================================

def get_query_param(nome):
    try:
        value = st.query_params.get(nome)
        if isinstance(value, list):
            return value[0] if value else ""
        return value or ""
    except Exception:
        try:
            value = st.experimental_get_query_params().get(nome, [""])
            return value[0] if value else ""
        except Exception:
            return ""


def backend_post(endpoint, payload):
    if not BACKEND_URL:
        raise ValueError("BACKEND_URL mancante nei Secrets.")

    url = f"{BACKEND_URL.rstrip('/')}{endpoint}"
    r = requests.post(url, json=payload, timeout=45)

    if r.status_code >= 400:
        raise ValueError(f"Errore backend {r.status_code}: {r.text}")

    return r.json()


def verifica_job_streamlit():
    job_id = get_query_param("job_id")
    token = get_query_param("token")

    if not job_id or not token:
        if REQUIRE_BACKEND_JOB:
            st.error("Accesso non autorizzato. Avvia questo report dal tuo account StoneSteel.")
            st.stop()
        return "", "", {"authorized": False, "dev_mode": True}

    data = backend_post("/jobs/verify", {"job_id": job_id, "token": token})

    if not data.get("authorized"):
        st.error("Accesso non autorizzato o credits insufficienti.")
        st.stop()

    return job_id, token, data


def notifica_successo(job_id, token, pdf_name):
    if not job_id or not token:
        return None
    return backend_post(
        "/jobs/complete",
        {
            "job_id": job_id,
            "token": token,
            "pdf_name": pdf_name
        }
    )


def notifica_fallimento(job_id, token, errore):
    if not job_id or not token:
        return None
    try:
        return backend_post(
            "/jobs/fail",
            {
                "job_id": job_id,
                "token": token,
                "error_message": str(errore)
            }
        )
    except Exception:
        return None


# ============================================================
# UTILITY
# ============================================================

def normalizza_targa(targa):
    return re.sub(r"[^A-Z0-9]", "", str(targa).upper().strip())


def pulisci_testo(testo):
    if testo is None:
        return ""

    testo = str(testo)

    sostituzioni = {
        "###": "",
        "##": "",
        "#": "",
        "**": "",
        "---": "",
        "€": "EUR",
        "–": "-",
        "—": "-",
        "’": "'",
        "“": '"',
        "”": '"',
        "•": "-",
        "\u00a0": " ",
        "\u2026": "...",
    }

    for k, v in sostituzioni.items():
        testo = testo.replace(k, v)

    testo = unicodedata.normalize("NFKD", testo)
    testo = testo.encode("latin-1", "ignore").decode("latin-1")

    return testo


def spezza(testo, max_len=38):
    parole = str(testo).split(" ")
    out = []

    for p in parole:
        if len(p) > max_len:
            out.append(" ".join([p[i:i+max_len] for i in range(0, len(p), max_len)]))
        else:
            out.append(p)

    return " ".join(out)


def flatten_json(data, prefix=""):
    rows = []

    if isinstance(data, dict):
        for k, v in data.items():
            new_prefix = f"{prefix}.{k}" if prefix else str(k)
            rows.extend(flatten_json(v, new_prefix))

    elif isinstance(data, list):
        for i, v in enumerate(data):
            rows.extend(flatten_json(v, f"{prefix}[{i}]"))

    else:
        if data is not None and str(data).strip():
            rows.append((prefix, str(data)))

    return rows


def cerca_valore(data, chiavi):
    for key, value in flatten_json(data):
        key_l = key.lower()
        for c in chiavi:
            if c.lower() in key_l:
                return value
    return ""


def estrai_dati_moto(dati):
    marca = cerca_valore(dati, ["make", "marca", "brand", "manufacturer", "CarMake", "vehicle.make"])
    modello = cerca_valore(dati, ["model", "modello", "version", "CarModel", "vehicle.model"])
    versione = cerca_valore(dati, ["version", "allestimento", "trim", "variant"])
    anno = cerca_valore(dati, ["year", "anno", "registrationYear", "firstRegistration", "immatricolazione"])
    cilindrata = cerca_valore(dati, ["cc", "engineCapacity", "cilindrata", "displacement"])
    alimentazione = cerca_valore(dati, ["fuel", "alimentazione"])
    telaio = cerca_valore(dati, ["vin", "telaio", "chassis", "numeroTelaio", "frame"])

    modello_preciso = " ".join([x for x in [marca, modello, versione] if x and x != "Non disponibile"]).strip()

    return {
        "marca": marca or "Non disponibile",
        "modello": modello or "Non disponibile",
        "versione": versione or "Non disponibile",
        "modello_preciso": modello_preciso or modello or "Non disponibile",
        "anno": anno or "Non disponibile",
        "cilindrata": cilindrata or "Non disponibile",
        "alimentazione": alimentazione or "Non disponibile",
        "telaio": telaio or "Non disponibile",
    }


def dati_to_testo(dati, titolo="Dati OpenAPI"):
    testo = titolo + "\n"

    for k, v in flatten_json(dati)[:120]:
        testo += f"- {k}: {v}\n"

    return testo


# ============================================================
# OPENAPI TARGA
# ============================================================

def chiama_openapi_targa(targa):
    if not OPENAPI_TOKEN:
        raise ValueError("OPENAPI_TOKEN mancante nei Secrets di Streamlit.")

    token = str(OPENAPI_TOKEN).strip()
    if token.lower().startswith("bearer "):
        raise ValueError("OPENAPI_TOKEN deve essere inserito senza la parola Bearer.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    url = f"{OPENAPI_TARGA_URL.rstrip('/')}/{targa}"

    r = requests.get(url, headers=headers, timeout=60)

    if r.status_code not in [200, 201, 202]:
        raise ValueError(f"Errore OpenAPI {r.status_code}: {r.text}")

    return r.json()


# ============================================================
# OPENAI REPORT
# ============================================================

def genera_report_targa(targa, dati_moto, dati_openapi):
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY mancante nei Secrets di Streamlit.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Genera un report motociclistico StoneSteel MotoCheck in italiano.

Il cliente ha inserito SOLO la targa. I dati tecnici arrivano da OpenAPI Automotive.
Devi scrivere come un meccanico esperto, concreto, diretto, professionale, che consiglia una persona prima di comprare una moto usata.

Targa:
{targa}

Dati moto estratti:
{json.dumps(dati_moto, ensure_ascii=False, indent=2)}

Dati OpenAPI completi:
{json.dumps(dati_openapi, ensure_ascii=False, indent=2)}

Il report deve essere lungo, pratico e leggibile.
Deve includere queste sezioni, con titoli semplici e senza markdown:

1. Identificazione della moto
Indica targa, marca, modello preciso, anno, cilindrata, alimentazione e telaio/VIN se disponibili.
Se un dato non è presente, scrivi "non disponibile".

2. Che moto è
Spiega il modello in modo chiaro: impostazione, tipo di utilizzo, pubblico tipico, carattere generale.

3. Cosa guarderei da meccanico
Descrivi in modo pratico quali parti controllare su quel modello: motore, trasmissione, frizione, cambio, elettronica, telaio, sospensioni, freni, scarichi, manutenzione, perdite, rumorosità.

4. Punti forti
Elenca e spiega i principali punti forti del modello.

5. Punti deboli e difetti ricorrenti
Elenca e spiega i problemi più probabili o tipici del modello, senza inventare richiami ufficiali non presenti nei dati.

6. Opinione StoneSteel Garage
Scrivi una valutazione estesa, come se stessi parlando al cliente davanti alla moto.
Deve essere concreta, non generica.

7. Quando comprarla
Spiega in quali condizioni vale la pena comprarla.

8. Quando evitarla
Spiega i segnali per lasciar perdere o trattare molto il prezzo.

9. Conclusione finale
Dai un consiglio finale: comprare, trattare, approfondire o evitare, motivando.

10. Checklist finale - 20 controlli prima dell'acquisto
Devi scrivere esattamente 20 punti numerati, specifici per questo modello quando possibile.
Ogni punto deve essere operativo, concreto e controllabile dal cliente.

Regole:
- NON usare markdown.
- NON usare simboli strani.
- NON usare URL.
- NON inventare dati ufficiali se non presenti.
- Scrivi in tono professionale ma umano, da meccanico/consulente esperto.
- Mantieni il report adatto a essere inserito in un PDF.
"""

    r = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Sei StoneSteel Garage: un consulente motociclistico esperto, tecnico, concreto e molto pratico sulle moto usate."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.35
    )

    return spezza(pulisci_testo(r.choices[0].message.content))


# ============================================================
# PDF
# ============================================================

class PDF(FPDF):

    def header(self):
        if os.path.exists(LOGO_PATH):
            try:
                self.image(LOGO_PATH, x=85, y=6, w=35)
            except Exception:
                pass

        self.ln(46)
        self.set_font("Helvetica", "B", 15)
        self.cell(0, 8, txt="StoneSteel MotoCheck", ln=True, align="C")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, txt=f"Pagina {self.page_no()}", align="C")


def pdf_sezione(pdf, titolo):
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 9, txt=pulisci_testo(titolo), ln=True, fill=True)
    pdf.ln(4)


def pdf_testo(pdf, testo):
    pdf.set_font("Helvetica", "", 10)
    testo = spezza(pulisci_testo(testo))

    for riga in testo.split("\n"):
        riga = riga.strip()
        if not riga:
            pdf.ln(2)
        else:
            pdf.multi_cell(180, 6, txt=riga)

    pdf.ln(3)


def estrai_checklist_da_report(testo_report):
    righe = []
    in_checklist = False

    for riga in str(testo_report).splitlines():
        r = riga.strip()
        if not r:
            continue

        r_low = r.lower()
        if "checklist" in r_low and ("20" in r_low or "controll" in r_low):
            in_checklist = True
            continue

        if in_checklist:
            if re.match(r"^\d+[\.\)]\s+", r):
                righe.append(r)
            elif righe and not re.match(r"^[A-ZÀ-Ù][A-Za-zÀ-ÿ\s]{2,40}$", r):
                righe[-1] += " " + r

    return righe[:20]


def crea_pdf(titolo, targa, dati_moto, testo_report):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(180, 9, txt=pulisci_testo(titolo))
    pdf.ln(6)

    pdf_sezione(pdf, "Targa")
    pdf_testo(pdf, targa)

    pdf_sezione(pdf, "Dati moto da OpenAPI")
    righe = ""
    for k, v in dati_moto.items():
        righe += f"- {k}: {v}\n"
    pdf_testo(pdf, righe)

    pdf_sezione(pdf, "Report StoneSteel")
    pdf_testo(pdf, testo_report)

    checklist = estrai_checklist_da_report(testo_report)
    if checklist:
        pdf.add_page()
        pdf_sezione(pdf, "Checklist finale - 20 controlli prima dell'acquisto")
        pdf_testo(pdf, "\n".join(checklist))

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return temp.name


# ============================================================
# UI PUBBLICA
# ============================================================

job_id, job_token, job_data = verifica_job_streamlit()

st.title("StoneSteel MotoCheck")
st.subheader("Report da targa")

st.write(
    "Inserisci solo la targa. StoneSteel identifica la moto tramite OpenAPI, recupera modello e telaio quando disponibili, "
    "poi genera un report PDF con valutazione tecnica, punti forti, punti deboli e checklist finale di 20 controlli."
)

if job_id:
    with st.expander("Sessione StoneSteel"):
        st.write(f"Tool autorizzato: {job_data.get('tool_name', 'report_targa')}")
        st.write(f"Credits previsti: {job_data.get('credits_cost', 'n/d')}")

targa_input = st.text_input("Targa")

if st.button("Genera Report da Targa"):

    if not targa_input:
        st.error("Inserisci la targa.")
    else:
        targa = normalizza_targa(targa_input)

        try:
            with st.spinner("Identificazione moto da targa tramite OpenAPI..."):
                dati_openapi = chiama_openapi_targa(targa)
                dati_moto = estrai_dati_moto(dati_openapi)

            st.success("Moto identificata.")
            st.json(dati_moto)

            with st.spinner("Generazione report StoneSteel..."):
                report = genera_report_targa(targa, dati_moto, dati_openapi)

            with st.spinner("Creazione PDF..."):
                pdf_path = crea_pdf(
                    titolo=f"Report StoneSteel da Targa - {targa}",
                    targa=targa,
                    dati_moto=dati_moto,
                    testo_report=report
                )

            pdf_name = f"StoneSteel_Report_Targa_{targa}.pdf"

            try:
                notifica_successo(job_id, job_token, pdf_name)
                if job_id:
                    st.success("Report generato correttamente. I credits sono stati scalati.")
            except Exception as e:
                st.warning(f"Report generato, ma notifica backend non riuscita: {e}")

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "Scarica Report PDF",
                    data=f,
                    file_name=pdf_name,
                    mime="application/pdf"
                )

            st.success("Report pronto.")

            with st.expander("Dettaglio dati OpenAPI"):
                st.json(dati_openapi)

        except Exception as e:
            notifica_fallimento(job_id, job_token, str(e))
            st.error(f"Errore generazione report: {e}")


# ============================================================
# NOTE TECNICHE
# ============================================================

with st.expander("Configurazione richiesta"):
    st.write("Secrets Streamlit necessari:")
    st.code("""
OPENAI_API_KEY="..."
OPENAPI_TOKEN="..."
OPENAPI_TARGA_URL="https://automotive.openapi.it/IT-bike"
BACKEND_URL="https://api.stonesteel.it"
REQUIRE_BACKEND_JOB="true"
LOGO_PATH="stonesteel_logo.png"
""")

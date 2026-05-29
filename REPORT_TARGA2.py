import os
import re
import json
import tempfile
import unicodedata
import requests
import smtplib
from email.message import EmailMessage

import streamlit as st
from openai import OpenAI
from fpdf import FPDF

try:
    import PyPDF2
except Exception:
    PyPDF2 = None


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
OPENAPI_TARGA_URL = secret("OPENAPI_TARGA_URL", "https://automotive.openapi.com/IT-bike")

PAYPAL_CLIENT_ID = secret("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = secret("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = secret("PAYPAL_MODE", "sandbox")
PAYPAL_RETURN_URL = secret("PAYPAL_RETURN_URL")
PAYPAL_CANCEL_URL = secret("PAYPAL_CANCEL_URL")

EMAIL_HOST = secret("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(secret("EMAIL_PORT", "587"))
EMAIL_USER = secret("EMAIL_USER")
EMAIL_PASSWORD = secret("EMAIL_PASSWORD")
EMAIL_FROM = secret("EMAIL_FROM", "StoneSteel MotoCheck <stonesteelshop@gmail.com>")
ADMIN_EMAIL = secret("ADMIN_EMAIL", "salvo.amandola@gmail.com")

ADMIN_PASSWORD = secret("ADMIN_PASSWORD", "admin")
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
    return {
        "marca": cerca_valore(dati, ["make", "marca", "brand", "manufacturer", "CarMake"]) or "Non disponibile",
        "modello": cerca_valore(dati, ["model", "modello", "version", "CarModel"]) or "Non disponibile",
        "anno": cerca_valore(dati, ["year", "anno", "registration"]) or "Non disponibile",
        "cilindrata": cerca_valore(dati, ["cc", "engine", "cilindrata", "displacement"]) or "Non disponibile",
        "alimentazione": cerca_valore(dati, ["fuel", "alimentazione"]) or "Non disponibile",
        "telaio": cerca_valore(dati, ["vin", "telaio", "chassis"]) or "Non disponibile",
    }


def dati_to_testo(dati, titolo="Dati"):
    testo = titolo + "\n"

    for k, v in flatten_json(dati)[:90]:
        testo += f"- {k}: {v}\n"

    return testo


# ============================================================
# OPENAPI TARGA
# ============================================================

def chiama_openapi_targa(targa):
    if not OPENAPI_TOKEN:
        raise ValueError("OPENAPI_TOKEN mancante nei Secrets.")

    if str(OPENAPI_TOKEN).lower().startswith("bearer "):
        raise ValueError("OPENAPI_TOKEN deve essere senza Bearer.")

    headers = {
        "Authorization": f"Bearer {OPENAPI_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    url = f"{OPENAPI_TARGA_URL.rstrip('/')}/{targa}"

    r = requests.get(url, headers=headers, timeout=60)

    if r.status_code not in [200, 201, 202]:
        raise ValueError(f"Errore OpenAPI {r.status_code}: {r.text}")

    return r.json()


# ============================================================
# PAYPAL API
# ============================================================

def paypal_base_url():
    if PAYPAL_MODE == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


def paypal_token():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise ValueError("Credenziali PayPal mancanti nei Secrets.")

    url = f"{paypal_base_url()}/v1/oauth2/token"

    r = requests.post(
        url,
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json"},
        timeout=60
    )

    if r.status_code not in [200, 201]:
        raise ValueError(f"Errore token PayPal {r.status_code}: {r.text}")

    return r.json()["access_token"]


def paypal_create_order(targa, email, tipo_report, importo):
    token = paypal_token()

    url = f"{paypal_base_url()}/v2/checkout/orders"

    body = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "description": f"StoneSteel MotoCheck - {tipo_report} - {targa}",
                "amount": {
                    "currency_code": "EUR",
                    "value": importo
                },
                "custom_id": f"{tipo_report}|{targa}|{email}"
            }
        ],
        "application_context": {
            "brand_name": "StoneSteel MotoCheck",
            "landing_page": "LOGIN",
            "user_action": "PAY_NOW",
            "return_url": PAYPAL_RETURN_URL,
            "cancel_url": PAYPAL_CANCEL_URL
        }
    }

    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=body,
        timeout=60
    )

    if r.status_code not in [200, 201]:
        raise ValueError(f"Errore creazione ordine PayPal {r.status_code}: {r.text}")

    data = r.json()

    approve_url = None
    for link in data.get("links", []):
        if link.get("rel") == "approve":
            approve_url = link.get("href")

    if not approve_url:
        raise ValueError("Link pagamento PayPal non trovato.")

    return data["id"], approve_url


def paypal_capture_order(order_id):
    token = paypal_token()

    url = f"{paypal_base_url()}/v2/checkout/orders/{order_id}/capture"

    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={},
        timeout=60
    )

    if r.status_code not in [200, 201]:
        raise ValueError(f"Errore capture PayPal {r.status_code}: {r.text}")

    data = r.json()

    if data.get("status") != "COMPLETED":
        raise ValueError(f"Pagamento non completato: {data.get('status')}")

    return data


# ============================================================
# OPENAI REPORT
# ============================================================

def genera_report_base(targa, dati_moto, dati_openapi):
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY mancante nei Secrets.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Genera un report motociclistico professionale StoneSteel.

Targa:
{targa}

Dati moto:
{json.dumps(dati_moto, ensure_ascii=False, indent=2)}

Dati OpenAPI:
{json.dumps(dati_openapi, ensure_ascii=False, indent=2)}

Il report deve includere:
1. Identificazione veicolo
2. Telaio / VIN se disponibile
3. Sintesi modello
4. Dati tecnici principali
5. Difetti ricorrenti del modello
6. Controlli usato
7. Valutazione StoneSteel Garage
8. Conclusione finale

NON usare markdown.
NON usare URL.
NON inventare dati ufficiali non presenti.
"""

    r = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Sei un esperto motociclistico professionale."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return spezza(pulisci_testo(r.choices[0].message.content))


def genera_report_pra_elaborato(targa, testo_pra, dati_moto_extra=""):
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY mancante nei Secrets.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Genera un report completo StoneSteel sulla base della visura PRA caricata.

Targa:
{targa}

Testo estratto dalla visura PRA:
{testo_pra}

Eventuali dati aggiuntivi:
{dati_moto_extra}

Il report deve includere:
1. Identificazione veicolo
2. Lettura dati PRA
3. Proprietà / formalità / gravami se presenti
4. Rischi documentali
5. Dati modello e criticità note
6. Valutazione StoneSteel Garage
7. Raccomandazione finale: comprare, trattare, evitare, approfondire

NON inventare dati.
Se un dato non è presente, scrivi che non è presente.
NON usare markdown.
"""

    r = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Sei un consulente esperto di moto usate e documentazione PRA."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25
    )

    return spezza(pulisci_testo(r.choices[0].message.content))


# ============================================================
# EMAIL
# ============================================================

def invia_email_admin_pra(email_cliente, targa, dati_moto, order_id):
    if not EMAIL_USER or not EMAIL_PASSWORD:
        raise ValueError("EMAIL_USER o EMAIL_PASSWORD mancanti nei Secrets.")

    msg = EmailMessage()
    msg["Subject"] = f"Nuova richiesta Report PRA StoneSteel - {targa}"
    msg["From"] = EMAIL_FROM
    msg["To"] = ADMIN_EMAIL

    corpo = f"""
Nuova richiesta Report PRA approfondito.

Pagamento PayPal verificato: COMPLETED
ID ordine PayPal: {order_id}

Email cliente:
{email_cliente}

Targa:
{targa}

Dati moto:
{json.dumps(dati_moto, ensure_ascii=False, indent=2)}

Procedere manualmente con visura PRA e consegna entro 36 ore.
"""

    msg.set_content(corpo)

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)


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


def crea_pdf(titolo, targa, dati_moto, testo_report):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(180, 9, txt=pulisci_testo(titolo))
    pdf.ln(6)

    pdf_sezione(pdf, "Targa")
    pdf_testo(pdf, targa)

    pdf_sezione(pdf, "Dati moto")
    righe = ""
    for k, v in dati_moto.items():
        righe += f"- {k}: {v}\n"
    pdf_testo(pdf, righe)

    pdf_sezione(pdf, "Report StoneSteel")
    pdf_testo(pdf, testo_report)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return temp.name


# ============================================================
# LETTURA PDF PRA ADMIN
# ============================================================

def estrai_testo_pdf(file):
    if PyPDF2 is None:
        raise ValueError("PyPDF2 non installato. Aggiungi PyPDF2 a requirements.txt.")

    reader = PyPDF2.PdfReader(file)
    testo = ""

    for page in reader.pages:
        testo += page.extract_text() or ""

    return testo


# ============================================================
# UI PUBBLICA
# ============================================================

st.title("StoneSteel MotoCheck")
st.subheader("Report da targa")

st.write(
    "Inserisci solo la targa. Potrai scegliere tra Report Base da 5 EUR o Report Approfondito con Visura PRA manuale da 30 EUR."
)

targa_input = st.text_input("Targa")
email_cliente = st.text_input("Email cliente")

tipo_report = st.selectbox(
    "Scegli il report",
    [
        "Report Base - 5 EUR",
        "Report Approfondito con Visura PRA - 30 EUR"
    ]
)

if "paypal_order_id" not in st.session_state:
    st.session_state.paypal_order_id = ""

if "pay_tipo" not in st.session_state:
    st.session_state.pay_tipo = ""

if "pay_targa" not in st.session_state:
    st.session_state.pay_targa = ""

if "pay_email" not in st.session_state:
    st.session_state.pay_email = ""


if st.button("Crea pagamento PayPal"):

    if not targa_input:
        st.error("Inserisci la targa.")
    elif not email_cliente:
        st.error("Inserisci email cliente.")
    else:
        try:
            targa = normalizza_targa(targa_input)

            if "Base" in tipo_report:
                importo = "5.00"
                tipo = "BASE"
            else:
                importo = "30.00"
                tipo = "PRA"

            with st.spinner("Creazione pagamento PayPal..."):
                order_id, approve_url = paypal_create_order(
                    targa=targa,
                    email=email_cliente,
                    tipo_report=tipo,
                    importo=importo
                )

            st.session_state.paypal_order_id = order_id
            st.session_state.pay_tipo = tipo
            st.session_state.pay_targa = targa
            st.session_state.pay_email = email_cliente

            st.success("Pagamento PayPal creato.")
            st.code(order_id)

            st.markdown(
                f"""
                <a href="{approve_url}" target="_blank">
                    <button style="
                        background-color:#f0c040;
                        color:black;
                        font-weight:bold;
                        border:none;
                        padding:12px 20px;
                        border-radius:10px;
                        cursor:pointer;
                        width:100%;
                    ">
                        Vai a PayPal
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )

        except Exception as e:
            st.error(f"Errore creazione pagamento: {e}")


st.markdown("---")
st.subheader("Dopo il pagamento")

order_id_input = st.text_input(
    "ID ordine PayPal",
    value=st.session_state.paypal_order_id
)

if st.button("Verifica pagamento e genera servizio"):

    if not order_id_input:
        st.error("Inserisci ID ordine PayPal.")
    else:
        try:
            with st.spinner("Verifica pagamento PayPal..."):
                pagamento = paypal_capture_order(order_id_input)

            st.success("Pagamento verificato: COMPLETED.")

            targa = st.session_state.pay_targa or normalizza_targa(targa_input)
            email_finale = st.session_state.pay_email or email_cliente
            tipo = st.session_state.pay_tipo

            with st.spinner("Identificazione moto da targa..."):
                dati_openapi = chiama_openapi_targa(targa)
                dati_moto = estrai_dati_moto(dati_openapi)

            st.json(dati_moto)

            if tipo == "BASE":
                with st.spinner("Generazione Report Base..."):
                    report = genera_report_base(targa, dati_moto, dati_openapi)
                    pdf_path = crea_pdf(
                        titolo=f"Report Base StoneSteel - {targa}",
                        targa=targa,
                        dati_moto=dati_moto,
                        testo_report=report
                    )

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Scarica Report Base PDF",
                        data=f,
                        file_name=f"StoneSteel_Report_Base_{targa}.pdf",
                        mime="application/pdf"
                    )

                st.success("Report Base generato.")

            else:
                with st.spinner("Invio email richiesta PRA a StoneSteel..."):
                    invia_email_admin_pra(
                        email_cliente=email_finale,
                        targa=targa,
                        dati_moto=dati_moto,
                        order_id=order_id_input
                    )

                st.success("Richiesta PRA inviata. StoneSteel procederà manualmente entro 36 ore.")

            with st.expander("Dettaglio pagamento PayPal"):
                st.json(pagamento)

        except Exception as e:
            st.error(f"Errore verifica/generazione: {e}")


# ============================================================
# AREA ADMIN NASCOSTA
# ============================================================

st.markdown("---")
st.subheader("Area admin StoneSteel")

password = st.text_input("Password admin", type="password")

if password == ADMIN_PASSWORD:

    st.success("Accesso admin effettuato.")

    targa_admin = st.text_input("Targa report PRA admin")
    dati_extra = st.text_area("Dati aggiuntivi moto / note interne")
    file_pra = st.file_uploader("Carica PDF Visura PRA", type=["pdf"])

    if st.button("Genera Report PRA elaborato"):

        if not targa_admin:
            st.error("Inserisci targa.")
        elif not file_pra:
            st.error("Carica PDF PRA.")
        else:
            try:
                with st.spinner("Lettura PDF PRA..."):
                    testo_pra = estrai_testo_pdf(file_pra)

                with st.spinner("Generazione report PRA elaborato..."):
                    report_pra = genera_report_pra_elaborato(
                        targa=normalizza_targa(targa_admin),
                        testo_pra=testo_pra,
                        dati_moto_extra=dati_extra
                    )

                dati_moto_admin = {
                    "targa": normalizza_targa(targa_admin),
                    "origine": "Visura PRA manuale caricata da admin"
                }

                pdf_path = crea_pdf(
                    titolo=f"Report PRA Approfondito StoneSteel - {normalizza_targa(targa_admin)}",
                    targa=normalizza_targa(targa_admin),
                    dati_moto=dati_moto_admin,
                    testo_report=report_pra
                )

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Scarica Report PRA elaborato",
                        data=f,
                        file_name=f"StoneSteel_Report_PRA_{normalizza_targa(targa_admin)}.pdf",
                        mime="application/pdf"
                    )

                st.success("Report PRA elaborato generato.")

            except Exception as e:
                st.error(f"Errore area admin: {e}")
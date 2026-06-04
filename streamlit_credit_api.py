"""
Modulo da copiare dentro le app Streamlit a pagamento.

Uso:
    from streamlit_credit_api import get_job_from_url, verify_job, notify_success, notify_failure

    job_id, token = get_job_from_url()
    verify_job(job_id, token)

    # dopo PDF generato:
    notify_success(job_id, token, pdf_name="report.pdf")
"""

import requests
import streamlit as st

BACKEND_URL = "http://127.0.0.1:8000"  # poi diventerà https://api.stonesteel.it

def get_job_from_url():
    job_id = st.query_params.get("job_id")
    token = st.query_params.get("token")

    if not job_id or not token:
        st.error("Accesso non autorizzato. Avvia il tool dal tuo account StoneSteel.")
        st.stop()

    return job_id, token

def verify_job(job_id: str, token: str):
    response = requests.post(
        f"{BACKEND_URL}/jobs/verify",
        json={"job_id": job_id, "token": token},
        timeout=30,
    )

    if response.status_code >= 400:
        st.error("Crediti insufficienti, sessione scaduta o accesso non valido.")
        st.stop()

    data = response.json()

    if not data.get("authorized"):
        st.error("Accesso non autorizzato.")
        st.stop()

    return data

def notify_success(job_id: str, token: str, pdf_name: str | None = None):
    response = requests.post(
        f"{BACKEND_URL}/jobs/complete",
        json={"job_id": job_id, "token": token, "pdf_name": pdf_name},
        timeout=30,
    )
    return response.json()

def notify_failure(job_id: str, token: str, error_message: str):
    response = requests.post(
        f"{BACKEND_URL}/jobs/fail",
        json={"job_id": job_id, "token": token, "error_message": error_message},
        timeout=30,
    )
    return response.json()

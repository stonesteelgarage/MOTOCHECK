ISTRUZIONI RAPIDE - STONESTEEL BACKEND

1) Apri il terminale nella cartella STONESTEEL_BACKEND

2) Crea ambiente virtuale:
python3 -m venv .venv

3) Attiva ambiente virtuale:
source .venv/bin/activate

4) Installa librerie:
pip3 install -r requirements.txt

5) Crea file .env:
copia .env.example e rinominalo .env

6) Inserisci nel file .env:
- PAYPAL_CLIENT_ID
- PAYPAL_CLIENT_SECRET
- SECRET_KEY
- STREAMLIT_SHARED_SECRET

7) Avvia backend:
uvicorn main:app --reload

8) Apri documentazione API:
http://127.0.0.1:8000/docs

FLUSSO BASE:
- /auth/register crea utente
- /auth/login restituisce token
- /paypal/create-order crea pagamento PayPal
- /paypal/capture-order accredita credits dopo pagamento
- /jobs/create crea job per Streamlit
- /jobs/verify viene chiamato da Streamlit
- /jobs/complete scala credits solo dopo PDF generato
- /jobs/fail libera i credits se il PDF fallisce

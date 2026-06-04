import requests
from fastapi import HTTPException
from config import PAYPAL_BASE_URL, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, FRONTEND_SUCCESS_URL, FRONTEND_CANCEL_URL

def get_paypal_access_token() -> str:
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Credenziali PayPal mancanti")

    response = requests.post(
        f"{PAYPAL_BASE_URL}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=30,
    )

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Errore autenticazione PayPal: {response.text}")

    return response.json()["access_token"]

def create_paypal_order(amount_eur: str, package_id: str) -> dict:
    token = get_paypal_access_token()

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": package_id,
                "amount": {
                    "currency_code": "EUR",
                    "value": amount_eur,
                },
            }
        ],
        "application_context": {
            "brand_name": "StoneSteel",
            "landing_page": "LOGIN",
            "user_action": "PAY_NOW",
            "return_url": FRONTEND_SUCCESS_URL,
            "cancel_url": FRONTEND_CANCEL_URL,
        },
    }

    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Errore creazione ordine PayPal: {response.text}")

    return response.json()

def capture_paypal_order(paypal_order_id: str) -> dict:
    token = get_paypal_access_token()

    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders/{paypal_order_id}/capture",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Errore capture PayPal: {response.text}")

    return response.json()

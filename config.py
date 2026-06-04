import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "StoneSteel Backend")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stonesteel.db")

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")

FRONTEND_SUCCESS_URL = os.getenv("FRONTEND_SUCCESS_URL", "https://stonesteel.it/payment-success")
FRONTEND_CANCEL_URL = os.getenv("FRONTEND_CANCEL_URL", "https://stonesteel.it/payment-cancel")

STREAMLIT_SHARED_SECRET = os.getenv("STREAMLIT_SHARED_SECRET", "CHANGE_ME_STREAMLIT")

PAYPAL_BASE_URL = (
    "https://api-m.sandbox.paypal.com"
    if PAYPAL_MODE == "sandbox"
    else "https://api-m.paypal.com"
)

CREDIT_PACKAGES = {
    "credits_10": {"credits": 10, "eur": "5.00"},
    "credits_20": {"credits": 20, "eur": "10.00"},
    "credits_50": {"credits": 50, "eur": "25.00"},
    "credits_100": {"credits": 100, "eur": "50.00"},
}

TOOL_COSTS = {
    "motocheck_report": 5,
    "annunci_report": 5,
    "questionario_moto": 3,
    "report_targa": 8,
}

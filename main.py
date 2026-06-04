from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import secrets

from database import Base, engine, get_db
from models import User, Wallet, CreditTransaction, PayPalOrder, Job
from schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    PayPalCreateOrderRequest, PayPalCaptureRequest,
    CreateJobRequest, VerifyJobRequest, CompleteJobRequest, FailJobRequest
)
from auth import hash_password, verify_password, create_access_token, get_current_user
from paypal_api import create_paypal_order, capture_paypal_order
from config import APP_NAME, CREDIT_PACKAGES, TOOL_COSTS

Base.metadata.create_all(bind=engine)

app = FastAPI(title=APP_NAME)


@app.get("/")
def root():
    return {"status": "ok", "app": APP_NAME}


# -----------------------
# AUTH
# -----------------------

@app.post("/auth/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    wallet = Wallet(user_id=user.id, credits_balance=0, credits_reserved=0)
    db.add(wallet)
    db.commit()

    token = create_access_token(user.id)
    return {"access_token": token}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login JSON per sito HTML/frontend.
    Body:
    {
      "email": "...",
      "password": "..."
    }
    """
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email o password errate")

    token = create_access_token(user.id)
    return {"access_token": token}


@app.post("/auth/token", response_model=TokenResponse)
def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login compatibile con il pulsante Authorize di Swagger/FastAPI.
    In Swagger usa:
    username = email
    password = password
    """
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email o password errate")

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


# -----------------------
# WALLET
# -----------------------

@app.get("/wallet")
def get_wallet(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "credits_balance": wallet.credits_balance,
        "credits_reserved": wallet.credits_reserved,
        "credits_available": wallet.credits_balance - wallet.credits_reserved,
    }


@app.get("/wallet/transactions")
def get_transactions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(CreditTransaction)
        .filter(CreditTransaction.user_id == current_user.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "type": r.type,
            "credits": r.credits,
            "amount_eur": r.amount_eur,
            "reference": r.reference,
            "created_at": r.created_at,
        }
        for r in rows
    ]


# -----------------------
# PAYPAL
# -----------------------

@app.get("/paypal/packages")
def paypal_packages():
    return CREDIT_PACKAGES


@app.post("/paypal/create-order")
def paypal_create_order(
    payload: PayPalCreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    package = CREDIT_PACKAGES.get(payload.package_id)
    if not package:
        raise HTTPException(status_code=400, detail="Pacchetto credits non valido")

    paypal_order = create_paypal_order(
        amount_eur=package["eur"],
        package_id=payload.package_id,
    )

    order_id = paypal_order["id"]

    row = PayPalOrder(
        paypal_order_id=order_id,
        user_id=current_user.id,
        package_id=payload.package_id,
        credits=package["credits"],
        amount_eur=package["eur"],
        status="created",
    )
    db.add(row)
    db.commit()

    approval_url = None
    for link in paypal_order.get("links", []):
        if link.get("rel") == "approve":
            approval_url = link.get("href")

    return {
        "paypal_order_id": order_id,
        "approval_url": approval_url,
        "raw": paypal_order,
    }


@app.post("/paypal/capture-order")
def paypal_capture_order(
    payload: PayPalCaptureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(PayPalOrder)
        .filter(
            PayPalOrder.paypal_order_id == payload.paypal_order_id,
            PayPalOrder.user_id == current_user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Ordine PayPal non trovato")

    if order.status == "completed":
        return {"status": "already_completed", "credits_added": 0}

    capture = capture_paypal_order(payload.paypal_order_id)

    if capture.get("status") != "COMPLETED":
        order.status = capture.get("status", "not_completed")
        db.commit()
        raise HTTPException(status_code=400, detail="Pagamento non completato")

    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    wallet.credits_balance += order.credits

    order.status = "completed"

    tx = CreditTransaction(
        user_id=current_user.id,
        type="purchase",
        credits=order.credits,
        amount_eur=order.amount_eur,
        reference=order.paypal_order_id,
    )

    db.add(tx)
    db.commit()

    return {
        "status": "completed",
        "credits_added": order.credits,
        "wallet_balance": wallet.credits_balance,
    }


# -----------------------
# JOBS PER STREAMLIT
# -----------------------

@app.get("/tools/costs")
def tools_costs():
    return TOOL_COSTS


@app.post("/jobs/create")
def create_job(
    payload: CreateJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    credits_cost = TOOL_COSTS.get(payload.tool_name)
    if credits_cost is None:
        raise HTTPException(status_code=400, detail="Tool non valido")

    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    available = wallet.credits_balance - wallet.credits_reserved

    if available < credits_cost:
        raise HTTPException(status_code=402, detail="Credits insufficienti")

    job_id = str(uuid.uuid4())
    streamlit_token = secrets.token_urlsafe(32)

    wallet.credits_reserved += credits_cost

    job = Job(
        id=job_id,
        user_id=current_user.id,
        tool_name=payload.tool_name,
        credits_cost=credits_cost,
        status="pending",
        streamlit_token=streamlit_token,
    )

    tx = CreditTransaction(
        user_id=current_user.id,
        type="reserve",
        credits=credits_cost,
        reference=job_id,
    )

    db.add(job)
    db.add(tx)
    db.commit()

    return {
        "job_id": job_id,
        "token": streamlit_token,
        "tool_name": payload.tool_name,
        "credits_reserved": credits_cost,
    }


@app.post("/jobs/verify")
def verify_job(payload: VerifyJobRequest, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == payload.job_id).first()

    if not job or job.streamlit_token != payload.token:
        raise HTTPException(status_code=401, detail="Job/token non valido")

    if job.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail=f"Job non utilizzabile: {job.status}")

    if job.status == "pending":
        job.status = "running"
        db.commit()

    return {
        "authorized": True,
        "job_id": job.id,
        "tool_name": job.tool_name,
        "credits_cost": job.credits_cost,
        "status": job.status,
    }


@app.post("/jobs/complete")
def complete_job(payload: CompleteJobRequest, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == payload.job_id).first()

    if not job or job.streamlit_token != payload.token:
        raise HTTPException(status_code=401, detail="Job/token non valido")

    if job.status == "completed":
        return {"status": "already_completed"}

    if job.status == "failed":
        raise HTTPException(status_code=400, detail="Job già fallito")

    wallet = db.query(Wallet).filter(Wallet.user_id == job.user_id).first()

    wallet.credits_reserved = max(0, wallet.credits_reserved - job.credits_cost)
    wallet.credits_balance = max(0, wallet.credits_balance - job.credits_cost)

    job.status = "completed"
    job.pdf_name = payload.pdf_name
    job.completed_at = datetime.utcnow()

    tx = CreditTransaction(
        user_id=job.user_id,
        type="consume",
        credits=job.credits_cost,
        reference=job.id,
    )

    db.add(tx)
    db.commit()

    return {
        "status": "completed",
        "credits_consumed": job.credits_cost,
        "wallet_balance": wallet.credits_balance,
    }


@app.post("/jobs/fail")
def fail_job(payload: FailJobRequest, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == payload.job_id).first()

    if not job or job.streamlit_token != payload.token:
        raise HTTPException(status_code=401, detail="Job/token non valido")

    if job.status == "completed":
        raise HTTPException(status_code=400, detail="Job già completato")

    wallet = db.query(Wallet).filter(Wallet.user_id == job.user_id).first()
    wallet.credits_reserved = max(0, wallet.credits_reserved - job.credits_cost)

    job.status = "failed"
    job.error_message = payload.error_message

    tx = CreditTransaction(
        user_id=job.user_id,
        type="release",
        credits=job.credits_cost,
        reference=job.id,
    )

    db.add(tx)
    db.commit()

    return {
        "status": "failed",
        "credits_released": job.credits_cost,
        "wallet_balance": wallet.credits_balance,
    }

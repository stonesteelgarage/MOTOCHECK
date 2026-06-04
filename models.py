from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    wallet = relationship("Wallet", back_populates="user", uselist=False)
    jobs = relationship("Job", back_populates="user")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    credits_balance = Column(Integer, default=0)
    credits_reserved = Column(Integer, default=0)

    user = relationship("User", back_populates="wallet")


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # purchase, reserve, consume, release, refund
    credits = Column(Integer, nullable=False)
    amount_eur = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PayPalOrder(Base):
    __tablename__ = "paypal_orders"

    id = Column(Integer, primary_key=True, index=True)
    paypal_order_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    package_id = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
    amount_eur = Column(String, nullable=False)
    status = Column(String, default="created")
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tool_name = Column(String, nullable=False)
    credits_cost = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    streamlit_token = Column(String, nullable=False)
    pdf_name = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="jobs")

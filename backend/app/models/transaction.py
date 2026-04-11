from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime


class Transaction(Base):
    __tablename__ = "transactions"

    id           = Column(Integer, primary_key=True, index=True)
    created_at   = Column(DateTime, default=datetime.datetime.utcnow)
    total_amount = Column(Float, default=0.0)
    items        = relationship("BillingItem", back_populates="transaction")


class BillingItem(Base):
    __tablename__ = "billing_items"

    id             = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    medicine_id    = Column(Integer, ForeignKey("medicines.id"))
    medicine_name  = Column(String)
    quantity       = Column(Integer)
    unit_price     = Column(Float)
    total_price    = Column(Float)
    transaction    = relationship("Transaction", back_populates="items")
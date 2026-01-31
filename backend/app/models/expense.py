"""Expense database model."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Index, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Expense(Base):
    """Expense record model."""
    
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Idempotency key to prevent duplicate entries on retries
    idempotency_key = Column(String(64), unique=True, nullable=True, index=True)
    
    # Currency support (feature 5)
    currency = Column(String(3), default="INR", nullable=False)
    original_amount = Column(Numeric(precision=12, scale=2), nullable=True)  # Amount in original currency
    exchange_rate = Column(Numeric(precision=12, scale=6), nullable=True)  # Rate used for conversion
    
    # Tags/Labels (feature 6) - stored as JSON array
    tags = Column(JSON, default=list, nullable=False)
    
    # Notes (feature 8)
    notes = Column(Text, nullable=True)
    
    # Attachment/Receipt (feature 7)
    attachment_url = Column(String(500), nullable=True)
    attachment_name = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="expenses")

    __table_args__ = (
        Index('ix_expenses_user_category', 'user_id', 'category'),
        Index('ix_expenses_user_date', 'user_id', 'date'),
    )

    def __repr__(self):
        return f"<Expense(id={self.id}, amount={self.amount}, category={self.category})>"

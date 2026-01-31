"""Recurring expense database model."""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship

from app.database import Base


class RecurringExpense(Base):
    """Recurring expense template for auto-creating expenses."""
    
    __tablename__ = "recurring_expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Expense details
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    
    # Recurrence settings
    frequency = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    day_of_week = Column(Integer, nullable=True)  # 0-6 for weekly (Mon=0)
    day_of_month = Column(Integer, nullable=True)  # 1-31 for monthly
    month_of_year = Column(Integer, nullable=True)  # 1-12 for yearly
    
    # Schedule
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # null = no end
    next_run_date = Column(Date, nullable=False, index=True)
    last_run_date = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    times_executed = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="recurring_expenses")

    def __repr__(self):
        return f"<RecurringExpense(id={self.id}, desc={self.description}, freq={self.frequency})>"


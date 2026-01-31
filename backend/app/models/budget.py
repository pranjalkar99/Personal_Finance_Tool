"""Budget database model."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Budget(Base):
    """Budget limit model for tracking spending limits per category."""
    
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    monthly_limit = Column(Numeric(precision=12, scale=2), nullable=False)
    alert_threshold = Column(Integer, default=80)  # Alert when spending reaches this % of limit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="budgets")

    __table_args__ = (
        UniqueConstraint('user_id', 'category', name='uq_user_category_budget'),
    )

    def __repr__(self):
        return f"<Budget(id={self.id}, category={self.category}, limit={self.monthly_limit})>"


"""Import/Export related Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class ImportRow(BaseModel):
    """Single row from import."""
    row_number: int
    date: str
    category: str
    description: str
    amount: str
    currency: Optional[str] = "INR"
    tags: Optional[str] = None
    notes: Optional[str] = None


class ImportError(BaseModel):
    """Error from import."""
    row_number: int
    error: str
    data: dict


class ImportResult(BaseModel):
    """Result of bulk import."""
    success_count: int
    error_count: int
    total_rows: int
    errors: List[ImportError]
    imported_ids: List[int]


class ImportPreview(BaseModel):
    """Preview of import before committing."""
    total_rows: int
    valid_rows: int
    invalid_rows: int
    preview_data: List[ImportRow]
    errors: List[ImportError]
    estimated_total: Decimal


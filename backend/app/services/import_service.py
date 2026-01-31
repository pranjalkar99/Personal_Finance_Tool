"""CSV Import service for bulk expense imports."""

import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Tuple, BinaryIO
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.user import User
from app.schemas.import_export import ImportResult, ImportError, ImportPreview, ImportRow
from app.schemas.expense import SUPPORTED_CURRENCIES


class ImportService:
    """Service for importing expenses from CSV."""

    def __init__(self, db: Session):
        self.db = db

    def parse_csv(self, file_content: str) -> Tuple[List[dict], List[ImportError]]:
        """Parse CSV content and return rows with any errors."""
        rows = []
        errors = []
        
        try:
            reader = csv.DictReader(io.StringIO(file_content))
            
            # Check required headers
            required_headers = {"date", "category", "description", "amount"}
            if not reader.fieldnames:
                errors.append(ImportError(
                    row_number=0,
                    error="No headers found in CSV file",
                    data={}
                ))
                return rows, errors
            
            headers = set(h.lower().strip() for h in reader.fieldnames)
            missing = required_headers - headers
            if missing:
                errors.append(ImportError(
                    row_number=0,
                    error=f"Missing required columns: {', '.join(missing)}",
                    data={}
                ))
                return rows, errors

            for row_num, row in enumerate(reader, start=2):
                # Normalize keys
                normalized = {k.lower().strip(): v.strip() if v else "" for k, v in row.items()}
                normalized["row_number"] = row_num
                rows.append(normalized)
                
        except Exception as e:
            errors.append(ImportError(
                row_number=0,
                error=f"CSV parsing error: {str(e)}",
                data={}
            ))
        
        return rows, errors

    def validate_row(self, row: dict) -> Tuple[bool, str, dict]:
        """Validate a single row and return (is_valid, error_message, cleaned_data)."""
        cleaned = {}
        
        # Date validation
        date_str = row.get("date", "")
        try:
            # Try multiple date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                try:
                    cleaned["date"] = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return False, f"Invalid date format: {date_str}", {}
        except Exception as e:
            return False, f"Date error: {str(e)}", {}

        # Amount validation
        amount_str = row.get("amount", "").replace(",", "").replace("₹", "").replace("$", "").replace("€", "").strip()
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                return False, "Amount must be positive", {}
            cleaned["amount"] = round(amount, 2)
        except (InvalidOperation, ValueError):
            return False, f"Invalid amount: {row.get('amount', '')}", {}

        # Category validation
        category = row.get("category", "").strip()
        if not category or len(category) > 100:
            return False, "Category is required (max 100 chars)", {}
        cleaned["category"] = category

        # Description validation
        description = row.get("description", "").strip()
        if not description or len(description) > 500:
            return False, "Description is required (max 500 chars)", {}
        cleaned["description"] = description

        # Currency (optional)
        currency = row.get("currency", "INR").upper().strip() or "INR"
        if currency not in SUPPORTED_CURRENCIES:
            currency = "INR"
        cleaned["currency"] = currency

        # Tags (optional)
        tags_str = row.get("tags", "")
        if tags_str:
            tags = [t.strip().lower() for t in tags_str.split(",") if t.strip()][:10]
            cleaned["tags"] = tags
        else:
            cleaned["tags"] = []

        # Notes (optional)
        notes = row.get("notes", "").strip()
        if notes and len(notes) <= 2000:
            cleaned["notes"] = notes
        else:
            cleaned["notes"] = None

        return True, "", cleaned

    def preview_import(self, user: User, file_content: str) -> ImportPreview:
        """Preview import without committing."""
        rows, parse_errors = self.parse_csv(file_content)
        
        preview_data = []
        validation_errors = []
        valid_count = 0
        total_amount = Decimal("0")

        for row in rows[:100]:  # Preview max 100 rows
            is_valid, error, cleaned = self.validate_row(row)
            
            if is_valid:
                valid_count += 1
                total_amount += cleaned["amount"]
                preview_data.append(ImportRow(
                    row_number=row["row_number"],
                    date=cleaned["date"].strftime("%Y-%m-%d"),
                    category=cleaned["category"],
                    description=cleaned["description"],
                    amount=str(cleaned["amount"]),
                    currency=cleaned.get("currency", "INR"),
                    tags=",".join(cleaned.get("tags", [])),
                    notes=cleaned.get("notes")
                ))
            else:
                validation_errors.append(ImportError(
                    row_number=row.get("row_number", 0),
                    error=error,
                    data=row
                ))

        all_errors = parse_errors + validation_errors
        
        return ImportPreview(
            total_rows=len(rows),
            valid_rows=valid_count,
            invalid_rows=len(validation_errors),
            preview_data=preview_data[:20],  # Show first 20 valid rows
            errors=all_errors[:20],  # Show first 20 errors
            estimated_total=total_amount
        )

    def import_expenses(self, user: User, file_content: str) -> ImportResult:
        """Import expenses from CSV."""
        rows, parse_errors = self.parse_csv(file_content)
        
        if parse_errors:
            return ImportResult(
                success_count=0,
                error_count=len(parse_errors),
                total_rows=len(rows),
                errors=parse_errors,
                imported_ids=[]
            )

        imported_ids = []
        validation_errors = []

        for row in rows:
            is_valid, error, cleaned = self.validate_row(row)
            
            if not is_valid:
                validation_errors.append(ImportError(
                    row_number=row.get("row_number", 0),
                    error=error,
                    data=row
                ))
                continue

            try:
                expense = Expense(
                    user_id=user.id,
                    amount=cleaned["amount"],
                    category=cleaned["category"],
                    description=cleaned["description"],
                    date=cleaned["date"],
                    currency=cleaned["currency"],
                    tags=cleaned["tags"],
                    notes=cleaned["notes"]
                )
                self.db.add(expense)
                self.db.flush()
                imported_ids.append(expense.id)
            except Exception as e:
                validation_errors.append(ImportError(
                    row_number=row.get("row_number", 0),
                    error=f"Database error: {str(e)}",
                    data=row
                ))

        if imported_ids:
            self.db.commit()

        return ImportResult(
            success_count=len(imported_ids),
            error_count=len(validation_errors),
            total_rows=len(rows),
            errors=validation_errors[:50],  # Limit errors in response
            imported_ids=imported_ids
        )


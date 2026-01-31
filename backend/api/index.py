"""Vercel serverless entry point."""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from app.main import app

# Export for Vercel
handler = app


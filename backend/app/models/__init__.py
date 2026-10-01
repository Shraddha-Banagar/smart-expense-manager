"""
Import all models here so that Base.metadata is aware of every table
when Base.metadata.create_all() or Alembic autogenerate is run.
"""
from app.models.user import User
from app.models.document import Document
from app.models.expense import Expense
from app.models.category import Category
from app.models.budget import Budget

__all__ = ["User", "Document", "Expense", "Category", "Budget"]

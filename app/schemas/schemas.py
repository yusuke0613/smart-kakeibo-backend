from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

# CategoryType の定義を追加
class CategoryType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class TransactionBase(BaseModel):
    amount: Decimal
    transaction_date: date
    description: Optional[str] = None
    major_category_id: int
    minor_category_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    transaction_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    user_id: int
    current_level: Optional[int] = None
    registration_date: date
    last_login_date: Optional[date] = None
    continuous_login_days: int
    total_login_days: int

    class Config:
        from_attributes = True

class MajorCategoryBase(BaseModel):
    name: str
    type: str  # 収入/支出
    is_fixed: bool = False

class MajorCategoryCreate(MajorCategoryBase):
    pass

class MajorCategory(MajorCategoryBase):
    major_category_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MinorCategoryBase(BaseModel):
    name: str
    major_category_id: int

class MinorCategoryCreate(MinorCategoryBase):
    pass

class MinorCategory(MinorCategoryBase):
    minor_category_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 一括登録用のスキーマを追加
class TransactionBulkCreate(BaseModel):
    transactions: List[TransactionCreate]

# 月次サマリー用のスキーマを追加
class CategorySummary(BaseModel):
    category_id: int
    category_name: str
    amount: Decimal

class MonthlySummary(BaseModel):
    yearmonth: str  # YYYYMM形式
    total_income: Decimal
    total_expense: Decimal
    income_categories: List[CategorySummary]
    expense_categories: List[CategorySummary]

class YearlySummary(BaseModel):
    year: int
    user_id: int
    monthly_summaries: List[MonthlySummary] 
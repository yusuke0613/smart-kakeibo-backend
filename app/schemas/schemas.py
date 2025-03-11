from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum, IntEnum

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

# 新しい列挙型を追加
class FamilyComposition(IntEnum):
    SINGLE = 1
    TWO_PERSON = 2
    THREE_PERSON = 3
    FOUR_PERSON = 4
    FIVE_PERSON = 5

class AgeGroup(IntEnum):
    TWENTIES = 1
    THIRTIES = 2
    FORTIES = 3
    FIFTIES = 4
    SIXTIES = 5

class IncomeRange(IntEnum):
    UNDER_3_5M = 1
    FROM_3_5M_TO_4M = 2
    FROM_4M_TO_5M = 3
    FROM_5M_TO_6M = 4
    FROM_6M_TO_7M = 5
    FROM_7M_TO_8M = 6
    FROM_8M_TO_9M = 7
    FROM_9M_TO_10M = 8
    FROM_10M_TO_12M = 9
    OVER_12M = 10

class LifestyleMindset(IntEnum):
    SAVING = 1
    BALANCED = 2
    COMFORT = 3

class MidtermGoal(IntEnum):
    NONE = 0
    INCREASE_SAVINGS = 1
    BUY_HOUSE = 2
    BUY_CAR = 3
    RETIREMENT_FUND = 4
    EDUCATION_FUND = 5
    HOBBY_TRAVEL_FUND = 6

class UserBase(BaseModel):
    username: str
    email: EmailStr
    family_composition: Optional[int] = None
    age_group: Optional[int] = None
    household_income_range: Optional[int] = None
    lifestyle_mindset: Optional[int] = None
    midterm_goal: Optional[int] = None
    monthly_expense_target: Optional[Decimal] = None

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

# ユーザープロファイル更新用のスキーマを追加
class UserProfileUpdate(BaseModel):
    family_composition: Optional[int] = None
    age_group: Optional[int] = None
    household_income_range: Optional[int] = None
    lifestyle_mindset: Optional[int] = None
    midterm_goal: Optional[int] = None
    monthly_expense_target: Optional[Decimal] = None

# 認証用スキーマ
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

# ユーザー存在確認用のスキーマ
class UserExistenceCheck(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserExistenceResponse(BaseModel):
    exists: bool
    field: Optional[str] = None  # username または email

# ユーザー情報更新用のスキーマ
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    family_composition: Optional[int] = None
    age_group: Optional[int] = None
    household_income_range: Optional[int] = None
    lifestyle_mindset: Optional[int] = None
    midterm_goal: Optional[int] = None
    monthly_expense_target: Optional[Decimal] = None 
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum

# CategoryType の定義を追加
class CategoryType(str, enum.Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    current_level = Column(Integer, ForeignKey("user_levels.level_id"))
    registration_date = Column(Date, default=func.current_date())
    last_login_date = Column(Date)
    continuous_login_days = Column(Integer, default=0)
    total_login_days = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    major_category_id = Column(Integer, ForeignKey("major_categories.major_category_id"))
    minor_category_id = Column(Integer, ForeignKey("minor_categories.minor_category_id"))
    amount = Column(Numeric(10, 2))
    transaction_date = Column(Date)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class MajorCategory(Base):
    __tablename__ = "major_categories"

    major_category_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    name = Column(String)
    type = Column(Enum(CategoryType))  # 型を修正
    is_fixed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    minor_categories = relationship("MinorCategory", back_populates="major_category")

class MinorCategory(Base):
    __tablename__ = "minor_categories"

    minor_category_id = Column(Integer, primary_key=True, index=True)
    major_category_id = Column(Integer, ForeignKey("major_categories.major_category_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    name = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    major_category = relationship("MajorCategory", back_populates="minor_categories") 
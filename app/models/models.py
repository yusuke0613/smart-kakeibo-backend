from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, ForeignKey, Text, Enum, text
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
    __table_args__ = {"schema": "kakeibo"}

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    level = relationship("UserLevel", back_populates="users")
    current_level = Column(Integer, ForeignKey("kakeibo.user_levels.level_id"))
    registration_date = Column(Date, server_default=text('CURRENT_DATE'))
    last_login_date = Column(Date)
    continuous_login_days = Column(Integer, server_default='0')
    total_login_days = Column(Integer, server_default='0')
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'), onupdate=text('now()'))

class Transaction(Base):
    __tablename__ = "transactions"      
    __table_args__ = {"schema": "kakeibo"}
    transaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("kakeibo.users.user_id"))
    major_category_id = Column(Integer, ForeignKey("kakeibo.major_categories.major_category_id"))
    minor_category_id = Column(Integer, ForeignKey("kakeibo.minor_categories.minor_category_id"))

    amount = Column(Numeric(10, 2))
    transaction_date = Column(Date)
    description = Column(Text)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'), onupdate=text('now()'))

class MajorCategory(Base):
    __tablename__ = "major_categories"
    __table_args__ = {"schema": "kakeibo"}
    major_category_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("kakeibo.users.user_id"))
    name = Column(String)
    type = Column(Enum(CategoryType))  # 型を修正
    is_fixed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'), onupdate=text('now()'))

    minor_categories = relationship("MinorCategory", back_populates="major_category")

class MinorCategory(Base):
    __tablename__ = "minor_categories"
    __table_args__ = {"schema": "kakeibo"}
    minor_category_id = Column(Integer, primary_key=True, index=True)
    major_category_id = Column(Integer, ForeignKey("kakeibo.major_categories.major_category_id"))
    user_id = Column(Integer, ForeignKey("kakeibo.users.user_id"))
    name = Column(String)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'), onupdate=text('now()'))

    major_category = relationship("MajorCategory", back_populates="minor_categories")

class UserLevel(Base):
    __tablename__ = "user_levels"
    __table_args__ = {"schema": "kakeibo"}

    level_id = Column(Integer, primary_key=True)
    level_name = Column(String, nullable=False)
    required_points = Column(Integer, server_default='0')
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'), onupdate=text('now()'))
    users = relationship("User", back_populates="level", foreign_keys=[User.current_level])
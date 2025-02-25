from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db.database import get_db
from app.models import models
from app.schemas import schemas
from enum import Enum
from pydantic import BaseModel

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/major", response_model=schemas.MajorCategory)
def create_major_category(
    category: schemas.MajorCategoryCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # 認証実装後に修正
):
    db_category = models.MajorCategory(
        **category.dict(),
        user_id=current_user_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/major", response_model=List[schemas.MajorCategory])
def read_major_categories(
    db: Session = Depends(get_db),
    current_user_id: int = 1
):
    return db.query(models.MajorCategory).filter(
        models.MajorCategory.user_id == current_user_id
    ).all()

@router.post("/minor", response_model=schemas.MinorCategory)
def create_minor_category(
    category: schemas.MinorCategoryCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1
):
    db_category = models.MinorCategory(
        **category.dict(),
        user_id=current_user_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/minor/{major_category_id}", response_model=List[schemas.MinorCategory])
def read_minor_categories(
    major_category_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1
):
    return db.query(models.MinorCategory).filter(
        models.MinorCategory.major_category_id == major_category_id,
        models.MinorCategory.user_id == current_user_id
    ).all()

# レスポンス用のスキーマを追加
class MinorCategoryResponse(BaseModel):
    minor_category_id: int
    name: str

class CategoryType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    # 他の必要な型があれば追加

class MajorCategoryWithMinors(BaseModel):
    major_category_id: int
    name: str
    type: CategoryType
    is_fixed: bool
    minor_categories: List[MinorCategoryResponse] = []

    class Config:
        from_attributes = True

# 既存のルーターに新しいエンドポイントを追加
@router.get("/user/{user_id}/all", response_model=List[MajorCategoryWithMinors])
def get_user_categories(
    user_id: int,
    db: Session = Depends(get_db)
):
    # ユーザーの存在確認
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 大カテゴリと紐づく小カテゴリを一括取得
    major_categories = db.query(models.MajorCategory)\
        .options(joinedload(models.MajorCategory.minor_categories))\
        .filter(models.MajorCategory.user_id == user_id)\
        .all()

    # レスポンスの整形
    result = []
    for major in major_categories:
        minor_categories = [
            MinorCategoryResponse(
                minor_category_id=minor.minor_category_id,
                name=minor.name
            ) for minor in major.minor_categories
        ]

        category_type = major.type
        if isinstance(category_type, str):
            category_type = category_type.lower()  # 小文字に変換

        result.append(MajorCategoryWithMinors(
            major_category_id=major.major_category_id,
            name=major.name,
            type=category_type,  # 修正された型を使用
            is_fixed=major.is_fixed,
            minor_categories=minor_categories
        ))

    return result 
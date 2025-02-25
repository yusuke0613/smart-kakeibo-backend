from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models import models
from app.schemas import schemas

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
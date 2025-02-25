from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db.database import get_db
from app.models import models
from app.schemas import schemas
from datetime import date, datetime
from calendar import monthrange

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/", response_model=schemas.Transaction)
def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # 認証実装後に修正
):
    db_transaction = models.Transaction(
        **transaction.dict(),
        user_id=current_user_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/", response_model=List[schemas.Transaction])
def read_transactions(
    skip: int = 0,
    limit: int = 100,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # 認証実装後に修正
):
    query = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user_id
    )
    
    if start_date:
        query = query.filter(models.Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.transaction_date <= end_date)
        
    return query.offset(skip).limit(limit).all()

@router.get("/{transaction_id}", response_model=schemas.Transaction)
def read_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # 認証実装後に修正
):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.transaction_id == transaction_id,
        models.Transaction.user_id == current_user_id
    ).first()
    
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

# レスポンス用のスキーマを修正
class TransactionWithCategoryNames(schemas.Transaction):
    major_category_name: str | None = None
    minor_category_name: str | None = None

    class Config:
        from_attributes = True

@router.get("/user/{user_id}/{yearmonth}", response_model=List[TransactionWithCategoryNames])
def get_user_transactions(
    user_id: int,
    yearmonth: str,  # YYYYMM形式
    db: Session = Depends(get_db)
):
    # ユーザーの存在確認
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # YYYYMM形式を解析
        year = int(yearmonth[:4])
        month = int(yearmonth[4:])
        
        # 月初と月末の日付を計算
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid yearmonth format. Please use YYYYMM (e.g., 202402)"
        )

    # トランザクションとカテゴリ名を一括取得
    transactions = db.query(
        models.Transaction,
        models.MajorCategory.name.label('major_category_name'),
        models.MinorCategory.name.label('minor_category_name')
    ).join(
        models.MajorCategory,
        models.Transaction.major_category_id == models.MajorCategory.major_category_id
    ).outerjoin(
        models.MinorCategory,
        models.Transaction.minor_category_id == models.MinorCategory.minor_category_id
    ).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.transaction_date >= start_date,
        models.Transaction.transaction_date <= end_date
    ).order_by(
        models.Transaction.transaction_date.desc()
    ).all()

    # レスポンスの整形
    result = []
    for record in transactions:
        transaction = record[0]
        transaction.major_category_name = record.major_category_name
        transaction.minor_category_name = record.minor_category_name
        result.append(transaction)

    return result 
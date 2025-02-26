from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db.database import get_db
from app.models import models
from app.schemas import schemas
from datetime import date, datetime
from calendar import monthrange
from sqlalchemy import func, and_, extract
from decimal import Decimal

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
    type: str | None = None

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

    # トランザクションとカテゴリ情報を一括取得
    transactions = db.query(
        models.Transaction,
        models.MajorCategory.name.label('major_category_name'),
        models.MinorCategory.name.label('minor_category_name'),
        models.MajorCategory.type.label('category_type')
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
        transaction.type = record.category_type
        result.append(transaction)

    return result

@router.post("/bulk", response_model=List[schemas.Transaction])
def create_transactions_bulk(
    transaction_data: schemas.TransactionBulkCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # 認証実装後に修正
):
    """
    複数のトランザクションを一括登録します。
    """
    if not transaction_data.transactions:
        raise HTTPException(status_code=400, detail="トランザクションデータが空です")
    
    db_transactions = []
    
    # 全てのトランザクションをデータベースに追加
    for transaction in transaction_data.transactions:
        db_transaction = models.Transaction(
            **transaction.dict(),
            user_id=current_user_id
        )
        db.add(db_transaction)
        db_transactions.append(db_transaction)
    
    # 一括コミット
    db.commit()
    
    # 全てのトランザクションをリフレッシュ
    for db_transaction in db_transactions:
        db.refresh(db_transaction)
    
    return db_transactions

@router.get("/summary/{user_id}/{year}", response_model=schemas.YearlySummary)
async def get_yearly_summary(
    user_id: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    指定された年とユーザーIDに基づいて、月ごとの収入・支出サマリーとカテゴリ別の金額を返します。
    """
    # ユーザーの存在確認
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # 年の妥当性チェック
    current_year = datetime.now().year
    if year < 2000 or year > current_year + 1:
        raise HTTPException(status_code=400, detail="無効な年が指定されています")

    # 月ごとのサマリーを格納するリスト
    monthly_summaries = []

    # 1月から12月までの各月のデータを取得
    for month in range(1, 13):
        # 月初と月末の日付を計算
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        # YYYYMM形式の文字列を作成
        yearmonth = f"{year}{month:02d}"

        # 収入カテゴリの合計を取得
        income_query = db.query(
            models.MajorCategory.major_category_id.label('category_id'),
            models.MajorCategory.name.label('category_name'),
            func.sum(models.Transaction.amount).label('amount')
        ).join(
            models.Transaction,
            models.Transaction.major_category_id == models.MajorCategory.major_category_id
        ).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.transaction_date >= start_date,
            models.Transaction.transaction_date <= end_date,
            models.MajorCategory.type == "INCOME"
        ).group_by(
            models.MajorCategory.major_category_id,
            models.MajorCategory.name
        ).all()

        # 支出カテゴリの合計を取得
        expense_query = db.query(
            models.MajorCategory.major_category_id.label('category_id'),
            models.MajorCategory.name.label('category_name'),
            func.sum(models.Transaction.amount).label('amount')
        ).join(
            models.Transaction,
            models.Transaction.major_category_id == models.MajorCategory.major_category_id
        ).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.transaction_date >= start_date,
            models.Transaction.transaction_date <= end_date,
            models.MajorCategory.type == "EXPENSE"
        ).group_by(
            models.MajorCategory.major_category_id,
            models.MajorCategory.name
        ).all()

        # 収入と支出の合計を計算
        total_income = db.query(
            func.sum(models.Transaction.amount)
        ).join(
            models.MajorCategory,
            models.Transaction.major_category_id == models.MajorCategory.major_category_id
        ).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.transaction_date >= start_date,
            models.Transaction.transaction_date <= end_date,
            models.MajorCategory.type == "INCOME"
        ).scalar() or Decimal('0.00')

        total_expense = db.query(
            func.sum(models.Transaction.amount)
        ).join(
            models.MajorCategory,
            models.Transaction.major_category_id == models.MajorCategory.major_category_id
        ).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.transaction_date >= start_date,
            models.Transaction.transaction_date <= end_date,
            models.MajorCategory.type == "EXPENSE"
        ).scalar() or Decimal('0.00')

        # カテゴリサマリーを作成
        income_categories = [
            schemas.CategorySummary(
                category_id=item.category_id,
                category_name=item.category_name,
                amount=item.amount
            ) for item in income_query
        ]

        expense_categories = [
            schemas.CategorySummary(
                category_id=item.category_id,
                category_name=item.category_name,
                amount=item.amount
            ) for item in expense_query
        ]

        # 月次サマリーを作成
        monthly_summary = schemas.MonthlySummary(
            yearmonth=yearmonth,
            total_income=total_income,
            total_expense=total_expense,
            income_categories=income_categories,
            expense_categories=expense_categories
        )

        monthly_summaries.append(monthly_summary)

    # 年間サマリーを作成して返却
    return schemas.YearlySummary(
        year=year,
        user_id=user_id,
        monthly_summaries=monthly_summaries
    )

@router.get("/monthly-summary/{user_id}", response_model=List[schemas.MonthlySummary])
async def get_monthly_summary(
    user_id: int,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db)
):
    """
    指定されたユーザーIDと期間に基づいて、YYYYMM形式でグループ化された収入・支出サマリーとカテゴリ別の金額を返します。
    期間が指定されない場合は、全期間のデータを返します。
    """
    # ユーザーの存在確認
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # トランザクションの日付をYYYYMM形式で抽出
    query = db.query(
        func.to_char(models.Transaction.transaction_date, 'YYYYMM').label('yearmonth'),
        models.MajorCategory.type.label('category_type'),
        models.MajorCategory.major_category_id.label('category_id'),
        models.MajorCategory.name.label('category_name'),
        func.sum(models.Transaction.amount).label('amount')
    ).join(
        models.MajorCategory,
        models.Transaction.major_category_id == models.MajorCategory.major_category_id
    ).filter(
        models.Transaction.user_id == user_id
    )
    
    # 期間フィルタの適用
    if start_date:
        query = query.filter(models.Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.transaction_date <= end_date)
    
    # グループ化と並べ替え
    result = query.group_by(
        'yearmonth',
        'category_type',
        'category_id',
        'category_name'
    ).order_by(
        'yearmonth',
        'category_type'
    ).all()
    
    # 結果をYYYYMM形式でグループ化
    yearmonth_groups = {}
    for record in result:
        yearmonth = record.yearmonth
        if yearmonth not in yearmonth_groups:
            yearmonth_groups[yearmonth] = {
                'income_categories': [],
                'expense_categories': [],
                'total_income': Decimal('0.00'),
                'total_expense': Decimal('0.00')
            }
        
        # カテゴリタイプに基づいて分類
        if record.category_type == "INCOME":
            yearmonth_groups[yearmonth]['income_categories'].append(
                schemas.CategorySummary(
                    category_id=record.category_id,
                    category_name=record.category_name,
                    amount=record.amount
                )
            )
            yearmonth_groups[yearmonth]['total_income'] += record.amount
        else:  # EXPENSE
            yearmonth_groups[yearmonth]['expense_categories'].append(
                schemas.CategorySummary(
                    category_id=record.category_id,
                    category_name=record.category_name,
                    amount=record.amount
                )
            )
            yearmonth_groups[yearmonth]['total_expense'] += record.amount
    
    # 月次サマリーのリストを作成
    monthly_summaries = []
    for yearmonth, data in sorted(yearmonth_groups.items()):
        monthly_summary = schemas.MonthlySummary(
            yearmonth=yearmonth,
            total_income=data['total_income'],
            total_expense=data['total_expense'],
            income_categories=data['income_categories'],
            expense_categories=data['expense_categories']
        )
        monthly_summaries.append(monthly_summary)
    
    return monthly_summaries 
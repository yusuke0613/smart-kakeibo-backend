from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas import schemas
from app.models.models import User
from app.core.security import get_password_hash, create_access_token
from datetime import timedelta
from app.core.config import settings
from datetime import datetime

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.Token)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    新しいユーザーを登録し、JWTトークンを発行します。
    """
    # ユーザー名が既に存在するか確認
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="このユーザー名は既に使用されています")
    
    # メールアドレスが既に存在するか確認
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="このメールアドレスは既に使用されています")
    
    # パスワードをハッシュ化
    hashed_password = get_password_hash(user.password)
    
    # 新しいユーザーを作成
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        current_level=1,  # デフォルトレベル
        registration_date=datetime.now().date(),
        continuous_login_days=1,
        total_login_days=1,
        last_login_date=datetime.now().date(),
        # プロファイル情報があれば追加
        family_composition=getattr(user, 'family_composition', None),
        age_group=getattr(user, 'age_group', None),
        household_income_range=getattr(user, 'household_income_range', None),
        lifestyle_mindset=getattr(user, 'lifestyle_mindset', None),
        midterm_goal=getattr(user, 'midterm_goal', None),
        monthly_expense_target=getattr(user, 'monthly_expense_target', None)
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # JWTトークンの生成
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.user_id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }

@router.put("/{user_id}/profile", response_model=schemas.User)
def update_user_profile(
    user_id: int,
    profile_data: schemas.UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    ユーザープロファイル情報を更新します。
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # 更新対象のフィールドを取得
    update_data = profile_data.dict(exclude_unset=True)
    
    # ユーザーオブジェクトを更新
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.post("/check-existence", response_model=schemas.UserExistenceResponse)
def check_user_existence(
    check_data: schemas.UserExistenceCheck,
    db: Session = Depends(get_db)
):
    """
    ユーザー名またはメールアドレスが既に登録されているか確認します。
    """
    if not check_data.username and not check_data.email:
        raise HTTPException(status_code=400, detail="ユーザー名またはメールアドレスを指定してください")
    
    # ユーザー名の存在確認
    if check_data.username:
        user = db.query(User).filter(User.username == check_data.username).first()
        if user:
            return {"exists": True, "field": "username"}
    
    # メールアドレスの存在確認
    if check_data.email:
        user = db.query(User).filter(User.email == check_data.email).first()
        if user:
            return {"exists": True, "field": "email"}
    
    # 存在しない場合
    return {"exists": False}

@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db)
):
    """
    ユーザー情報を更新します。
    """
    # ユーザーの存在確認
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # 更新データの準備
    update_data = user_data.dict(exclude_unset=True)
    
    # ユーザー名の重複確認
    if "username" in update_data and update_data["username"] != user.username:
        existing_user = db.query(User).filter(User.username == update_data["username"]).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="このユーザー名は既に使用されています")
    
    # メールアドレスの重複確認
    if "email" in update_data and update_data["email"] != user.email:
        existing_user = db.query(User).filter(User.email == update_data["email"]).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="このメールアドレスは既に使用されています")
    
    # パスワードのハッシュ化
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    # ユーザー情報の更新
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user 
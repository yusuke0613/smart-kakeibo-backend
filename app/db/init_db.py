from sqlalchemy.orm import Session
from app.models.models import UserLevel
from sqlalchemy import text

def init_user_levels(db: Session):
    # テーブルが空かどうかを確認
    result = db.execute(text("SELECT COUNT(*) FROM kakeibo.user_levels")).scalar()
    
    if result == 0:  # テーブルが空の場合のみ初期データを挿入
        levels = [
            UserLevel(level_id=1, level_name="初心者", required_points=0),
            UserLevel(level_id=2, level_name="中級者", required_points=100),
            UserLevel(level_id=3, level_name="上級者", required_points=500),
        ]
        try:
            db.bulk_save_objects(levels)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error inserting initial user levels: {e}") 
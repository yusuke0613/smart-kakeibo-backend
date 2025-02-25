from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
from app.db.database import Base

# 個別にすべてのモデルをインポート
from app.models.models import User  # Userモデルを明示的にインポート
# 他の必要なモデルもここで明示的にインポート
from app.models.models import MajorCategory, MinorCategory  # 例
from app.models.models import Transaction  # 例

from app.core.config import settings
# スキーマ名を定義
SCHEMA_NAME = "kakeibo"

# Alembic Config オブジェクト
config = context.config

# alembic.iniのURLを環境変数から設定
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        return object.schema == SCHEMA_NAME
    return True

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        include_object=include_object,
        version_table_schema=SCHEMA_NAME
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # スキーマを作成
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
            version_table_schema=SCHEMA_NAME,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
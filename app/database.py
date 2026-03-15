from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import settings

db_url = settings.DATABASE_URL

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(db_url, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Алиас для совместимости с роутерами
get_session = get_db


async def migrate_db():
    """Добавляет новые колонки в существующие таблицы"""
    async with engine.begin() as conn:
        # Добавляем is_admin если нет
        try:
            await conn.execute(text(
                "ALTER TABLE doctors ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"
            ))
            print("✅ Колонка is_admin добавлена")
        except Exception as e:
            print(f"⚠️ is_admin: {e}")

        # Добавляем username если нет
        try:
            await conn.execute(text(
                "ALTER TABLE doctors ADD COLUMN IF NOT EXISTS username VARCHAR UNIQUE"
            ))
            print("✅ Колонка username добавлена")
        except Exception as e:
            print(f"⚠️ username: {e}")

        # NEW: Добавляем subscription_until в pets если нет
        try:
            await conn.execute(text(
                "ALTER TABLE pets ADD COLUMN IF NOT EXISTS subscription_until TIMESTAMP NULL"
            ))
            print("✅ Колонка subscription_until добавлена")
        except Exception as e:
            print(f"⚠️ subscription_until: {e}")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Миграция существующих таблиц
    await migrate_db()

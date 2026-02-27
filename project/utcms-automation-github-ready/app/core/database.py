from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.core.config import utcms_config

# ایجاد موتور دیتابیس آسنکرون
engine = create_async_engine(utcms_config.DATABASE_URL, echo=False, future=True)


async def init_db():
    """ایجاد جداول دیتابیس در هنگام راه‌اندازی"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    """وابستگی برای دریافت سشن دیتابیس"""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

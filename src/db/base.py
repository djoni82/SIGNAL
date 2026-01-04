# src/db/base.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Use sqlite for simplicity in this refactor unless configured otherwise
DATABASE_URL = "sqlite+aiosqlite:///./bot.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# src/db/models.py
# (Placeholder for future models)
class Trade(Base):
    __tablename__ = 'trades'
    # Define columns here...
    pass

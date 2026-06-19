import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool, SingletonThreadPool
import datetime
from tenacity import retry, wait_exponential, stop_after_attempt
from config import settings

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(255))
    fault_type = Column(String(255))
    confidence = Column(Float)
    timestamp = Column(String(255), default=lambda: datetime.datetime.utcnow().isoformat())

DB_PATH = os.path.join(settings.DATA_DIR, "self_healing.db")
DB_URL = settings.DATABASE_URL or f"sqlite:///{DB_PATH}"

# Connection Pooling Configuration
if DB_URL.startswith("sqlite"):
    engine = create_engine(
        DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=SingletonThreadPool
    )
else:
    engine = create_engine(
        DB_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(5))
def get_db_session():
    """Returns a new DB session with retry logic for reliability (Phase 6)."""
    return SessionLocal()

def init_db() -> None:
    # Alembic handles migrations, but we can do a base create_all for initial setup
    Base.metadata.create_all(bind=engine)

def get_connection():
    """Legacy wrapper for compatibility with raw cursor logic in other files."""
    # We will refactor other files to use SQLAlchemy sessions eventually
    # For now, return the raw DBAPI connection.
    return engine.raw_connection()

_MAX_EVENTS = 10_000

def prune_events() -> None:
    session = get_db_session()
    try:
        count = session.query(Event).count()
        if count > _MAX_EVENTS:
            excess = count - _MAX_EVENTS
            ids_to_delete = session.query(Event.id).order_by(Event.id.asc()).limit(excess).all()
            if ids_to_delete:
                ids = [r[0] for r in ids_to_delete]
                session.query(Event).filter(Event.id.in_(ids)).delete(synchronize_session=False)
                session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

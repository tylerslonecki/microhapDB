from sqlalchemy import create_engine
from src.models import SYNC_DATABASE_URL
from sqlalchemy.orm import sessionmaker
from src.models import Sequence


sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)


# Configure sessionmaker for synchronous usage
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)
def get_sync_session():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
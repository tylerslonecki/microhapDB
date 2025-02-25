# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from src.models import DATABASE_URL
# from sqlalchemy.orm import sessionmaker
# from src.models import Sequence
#
#
# engine = create_async_engine(DATABASE_URL, echo=True)
#
# AsyncSessionLocal = sessionmaker(
#     bind=engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
#     autocommit=False,
#     autoflush=False,
# )
#
# async def get_session():
#     async with AsyncSessionLocal() as session:
#         yield session
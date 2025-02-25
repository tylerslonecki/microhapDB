# # brapi_endpoints.py
#
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy import select, func
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import Session
# from .brapi_models import BrAPIVariantResponse, Metadata, BrAPIVariant
# from .models import Sequence, get_session
#
# brapi_router = APIRouter()
#
# @brapi_router.get("/v2/{species}/variants", response_model=BrAPIVariantResponse)
# async def get_variants(
#     species: str,
#     page: int = 0,
#     pageSize: int = 1000,
#     db: AsyncSession = Depends(get_session)
# ):
#     valid_species = ["sweetpotato", "blueberry", "alfalfa", "cranberry"]
#     if species not in valid_species:
#         raise HTTPException(status_code=400, detail="Invalid species provided.")
#
#     count_stmt = select(func.count()).where(Sequence.species == species)
#     total_result = await db.execute(count_stmt)
#     total_count = total_result.scalar()
#     total_pages = (total_count + pageSize - 1) // pageSize
#
#     result = await db.execute(count_stmt.offset(page * pageSize).limit(pageSize))
#     sequences = result.scalars().all()
#
#     variants = [
#         BrAPIVariant(
#             variantDbId=str(seq.hapid),
#             variantName=seq.alleleid,
#             # Map other fields as necessary
#         ) for seq in sequences
#     ]
#
#     metadata = Metadata(
#         pagination={
#             "pageSize": pageSize,
#             "currentPage": page,
#             "totalCount": total_count,
#             "totalPages": total_pages
#         },
#         status=[],
#         datafiles=[]
#     )
#
#     return BrAPIVariantResponse(metadata=metadata, result=variants)
#

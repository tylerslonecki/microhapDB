# brapi_endpoints.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .brapi_models import BrAPIVariantResponse, Metadata, BrAPIVariant
from .models import Sequence, get_sync_session

brapi_router = APIRouter()

@brapi_router.get("/v2/{species}/variants", response_model=BrAPIVariantResponse)
async def get_variants(
    species: str,
    page: int = 0,
    pageSize: int = 1000,
    db: Session = Depends(get_sync_session)
):
    #Should dynamically retrieve from list of species in DB
    valid_species = ["sweetpotato", "blueberry", "alfalfa", "cranberry"]
    if species not in valid_species:
        raise HTTPException(status_code=400, detail="Invalid species provided.")

    query = db.query(Sequence).filter(Sequence.species == species)
    total_count = query.count()
    total_pages = (total_count + pageSize - 1) // pageSize
    sequences = query.offset(page * pageSize).limit(pageSize).all()

    variants = [
        BrAPIVariant(
            variantDbId=str(seq.hapid),
            variantName=seq.alleleid,
            # Map other fields as necessary
        ) for seq in sequences
    ]

    metadata = Metadata(
        pagination={
            "pageSize": pageSize,
            "currentPage": page,
            "totalCount": total_count,
            "totalPages": total_pages
        },
        status=[],
        datafiles=[]
    )

    return BrAPIVariantResponse(metadata=metadata, result=variants)

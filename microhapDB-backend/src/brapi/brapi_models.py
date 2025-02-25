# # brapi_models.py
#
# from pydantic import BaseModel
# from typing import List, Optional
#
# class Metadata(BaseModel):
#     pagination: Optional[dict]
#     status: Optional[List[dict]]
#     datafiles: Optional[List[str]]
#
# class BrAPIVariant(BaseModel):
#     variantDbId: str
#     variantName: str
#     # Add other required fields
#
# class BrAPIVariantResponse(BaseModel):
#     metadata: Metadata
#     result: List[BrAPIVariant]

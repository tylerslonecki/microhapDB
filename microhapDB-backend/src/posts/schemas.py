from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict

class BatchSummary(BaseModel):
    batch_id: int
    date: datetime
    new_sequences: int

class UploadSummary(BaseModel):
    total_unique_sequences: int
    new_sequences_this_batch: int
    batch_history: List[BatchSummary]

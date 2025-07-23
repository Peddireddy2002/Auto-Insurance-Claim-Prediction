from pydantic import BaseModel
from typing import Optional

class ClaimData(BaseModel):
    claim: str
    amount: Optional[float] = 0.0

class UploadResponse(BaseModel):
    filename: str
    path: str
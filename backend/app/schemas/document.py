from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    filename: str
    file_url: str
    file_type: str
    ocr_text: Optional[str] = None
    processing_status: str
    uploaded_at: datetime

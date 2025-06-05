from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class LogEntryBase(BaseModel):
    upload_id: int
    timestamp: datetime
    log_level: str
    source: str
    message: str
    additional_fields: Optional[Dict[str, Any]] = None

class LogEntryCreate(LogEntryBase):
    pass

class LogEntryInDB(LogEntryBase):
    id: int

    class Config:
        from_attributes = True

class LogEntryResponse(LogEntryInDB):
    pass

class LogEntryUpdate(BaseModel):
    log_level: Optional[str] = None
    message: Optional[str] = None
    additional_fields: Optional[Dict[str, Any]] = None

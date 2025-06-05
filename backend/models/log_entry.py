from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from .base import Base

class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    log_level = Column(String, index=True, nullable=False)
    source = Column(String, index=True, nullable=False)
    message = Column(String, nullable=False)
    additional_fields = Column(JSON, nullable=True)

    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_log_level', 'log_level'),
        Index('idx_source', 'source'),
        Index('idx_timestamp', 'timestamp'),
    )

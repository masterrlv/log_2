from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.log_entry import LogEntry

def get_log_entry(db: Session, log_id: int) -> Optional[LogEntry]:
    return db.query(LogEntry).filter(LogEntry.id == log_id).first()

def get_log_entries(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    log_level: Optional[str] = None,
    source: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[LogEntry]:
    query = db.query(LogEntry)
    
    if log_level:
        query = query.filter(LogEntry.log_level == log_level.upper())
    if source:
        query = query.filter(LogEntry.source == source)
    if start_time:
        query = query.filter(LogEntry.timestamp >= start_time)
    if end_time:
        query = query.filter(LogEntry.timestamp <= end_time)
    
    return query.offset(skip).limit(limit).all()

def search_logs(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 100,
) -> List[LogEntry]:
    return (
        db.query(LogEntry)
        .filter(LogEntry.message.ilike(f"%{query}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_log_entry(db: Session, log_data: Dict[str, Any]) -> LogEntry:
    db_log = LogEntry(**log_data)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def bulk_create_log_entries(db: Session, logs: List[Dict[str, Any]]) -> None:
    db.bulk_insert_mappings(LogEntry, logs)
    db.commit()

def get_log_statistics(
    db: Session,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    query = db.query(
        LogEntry.log_level,
        func.count(LogEntry.id).label("count")
    )
    
    if start_time:
        query = query.filter(LogEntry.timestamp >= start_time)
    if end_time:
        query = query.filter(LogEntry.timestamp <= end_time)
    
    results = query.group_by(LogEntry.log_level).all()
    return {level: count for level, count in results}

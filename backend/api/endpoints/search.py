from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from backend.models import log_entry as log_entry_models, user as user_models
from backend.schemas import log_entry as log_entry_schemas, search as search_schemas
from backend.services.database import get_db
from backend.services.auth import get_current_active_user
from backend.crud import log_entry as log_entry_crud

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/logs", response_model=schemas.LogSearchResponse)
def search_logs(
    q: Optional[str] = None,
    log_level: Optional[str] = None,
    source: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = 1,
    per_page: int = 20,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search logs with various filters and pagination
    """
    skip = (page - 1) * per_page
    
    # Build query filters
    query_filters = {}
    if log_level:
        query_filters["log_level"] = log_level.upper()
    if source:
        query_filters["source"] = source
    if start_time:
        query_filters["start_time"] = start_time
    if end_time:
        query_filters["end_time"] = end_time
    
    # Execute search
    if q:
        # Full-text search
        logs = log_entry_crud.search_logs(
            db=db,
            query=q,
            skip=skip,
            limit=per_page,
            **query_filters
        )
        total = log_entry_crud.count_logs(
            db=db,
            query=q,
            **query_filters
        )
    else:
        # Filtered search
        logs = log_entry_crud.get_log_entries(
            db=db,
            skip=skip,
            limit=per_page,
            **query_filters
        )
        total = log_entry_crud.count_logs(
            db=db,
            **{k: v for k, v in query_filters.items() if k not in ['skip', 'limit']}
        )
    
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@router.get("/analytics/time-series", response_model=List[schemas.TimeSeriesResponse])
def get_time_series(
    start_time: datetime,
    end_time: datetime,
    interval: str = "hour",
    log_level: Optional[str] = None,
    source: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get time series data for log events
    """
    if interval not in ["minute", "hour", "day"]:
        raise HTTPException(status_code=400, detail="Interval must be one of: minute, hour, day")
    
    return log_entry_crud.get_time_series(
        db=db,
        start_time=start_time,
        end_time=end_time,
        interval=interval,
        log_level=log_level,
        source=source
    )

@router.get("/analytics/distribution", response_model=List[schemas.DistributionResponse])
def get_distribution(
    field: str = "log_level",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get distribution of log events by field
    """
    if field not in ["log_level", "source"]:
        raise HTTPException(status_code=400, detail="Field must be one of: log_level, source")
    
    return log_entry_crud.get_distribution(
        db=db,
        field=field,
        start_time=start_time,
        end_time=end_time
    )

@router.get("/analytics/top-errors", response_model=List[schemas.ErrorResponse])
def get_top_errors(
    limit: int = 10,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get most common error messages
    """
    return log_entry_crud.get_top_errors(
        db=db,
        limit=limit,
        start_time=start_time,
        end_time=end_time
    )

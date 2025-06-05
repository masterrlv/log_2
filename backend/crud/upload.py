from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..models.upload import Upload

def get_upload(db: Session, upload_id: int) -> Optional[Upload]:
    return db.query(Upload).filter(Upload.id == upload_id).first()

def get_uploads(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    status: Optional[str] = None
) -> List[Upload]:
    query = db.query(Upload)
    
    if user_id is not None:
        query = query.filter(Upload.user_id == user_id)
    if status:
        query = query.filter(Upload.status == status)
    
    return query.offset(skip).limit(limit).all()

def create_upload(
    db: Session,
    user_id: int,
    filename: str,
    size: int,
    status: str = "pending"
) -> Upload:
    db_upload = Upload(
        user_id=user_id,
        filename=filename,
        size=size,
        status=status
    )
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    return db_upload

def update_upload_status(
    db: Session,
    upload_id: int,
    status: str,
    completed: bool = False
) -> Optional[Upload]:
    db_upload = get_upload(db, upload_id)
    if not db_upload:
        return None
    
    db_upload.status = status
    if completed:
        from sqlalchemy import func
        db_upload.completed_at = func.now()
    
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    return db_upload

def delete_upload(db: Session, upload_id: int) -> bool:
    db_upload = get_upload(db, upload_id)
    if not db_upload:
        return False
    
    db.delete(db_upload)
    db.commit()
    return True

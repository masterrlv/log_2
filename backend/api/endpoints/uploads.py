import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.models import upload as upload_models, user as user_models
from backend.schemas import upload as upload_schemas
from backend.services.database import get_db
from backend.services.auth import get_current_active_user
from backend.crud import upload as upload_crud, log_entry as log_entry_crud
from backend.tasks import process_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Ensure uploads directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=schemas.UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Save the uploaded file
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # Save file to disk
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create upload record
        db_upload = upload_crud.create_upload(
            db=db,
            user_id=current_user.id,
            filename=file.filename,
            size=len(content)
        )
        
        # Start background task to process the file
        process_upload.delay(db_upload.id, file_path)
        
        return db_upload
        
    except Exception as e:
        # Clean up file if something goes wrong
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )

@router.get("/", response_model=List[schemas.UploadResponse])
def list_uploads(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return upload_crud.get_uploads(
        db=db,
        skip=skip,
        limit=limit,
        user_id=current_user.id
    )

@router.get("/{upload_id}", response_model=schemas.UploadWithLogs)
def get_upload(
    upload_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get the upload
    db_upload = upload_crud.get_upload(db, upload_id=upload_id)
    if not db_upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Verify ownership (unless admin)
    if db_upload.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this upload")
    
    # Get associated logs
    logs = log_entry_crud.get_log_entries(
        db=db,
        upload_id=upload_id,
        limit=100  # Limit number of logs returned
    )
    
    return {
        **db_upload.__dict__,
        "logs": logs
    }

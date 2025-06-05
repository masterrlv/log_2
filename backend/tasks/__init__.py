from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime
import os

from ..services.database import SessionLocal
from ..models.upload import Upload
from ..models.log_entry import LogEntry
from ..services.log_parser import LogParserFactory
from ..crud.upload import update_upload_status
from ..crud.log_entry import bulk_create_log_entries

@shared_task(bind=True, max_retries=3)
def process_upload(self, upload_id: int, file_path: str):
    """Process uploaded log file in the background"""
    db = SessionLocal()
    try:
        # Update status to processing
        update_upload_status(db, upload_id, "processing")
        
        # Read and parse the file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Detect log format and get appropriate parser
        log_format = LogParserFactory.detect_format(lines)
        if not log_format:
            raise ValueError("Could not detect log format")
        
        parser = LogParserFactory.get_parser(log_format)
        
        # Parse logs
        parsed_logs = []
        for line in lines:
            log_entry = parser.parse_line(line.strip())
            if log_entry:
                log_entry['upload_id'] = upload_id
                parsed_logs.append(log_entry)
        
        # Bulk insert logs
        if parsed_logs:
            bulk_create_log_entries(db, parsed_logs)
        
        # Update status to completed
        update_upload_status(db, upload_id, "completed", completed=True)
        
        # Clean up the file
        try:
            os.remove(file_path)
        except OSError:
            pass
            
        return {"status": "success", "logs_processed": len(parsed_logs)}
        
    except Exception as e:
        # Update status to failed
        update_upload_status(db, upload_id, f"failed: {str(e)}")
        # Re-raise for Celery to handle retries
        raise self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes
        
    finally:
        db.close()

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel
from datetime import datetime
import jwt
import re
import os
from passlib.context import CryptContext
from celery import Celery

# FastAPI app setup
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Database setup
DATABASE_URL = "postgresql://logs:logs_db@localhost:5432/logs_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# Celery setup
celery = Celery('tasks', broker='redis://localhost:6379/0')
# Authentication setup
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="viewer")

class Upload(Base):
    __tablename__ = "uploads"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    filename = Column(String)
    size = Column(Integer)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="processing")

class LogEntry(Base):
    __tablename__ = "log_entries"
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer)
    timestamp = Column(DateTime)
    log_level = Column(String, index=True)
    source = Column(String, index=True)
    message = Column(String)
    additional_fields = Column(JSON)

Base.metadata.create_all(bind=engine)

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "viewer"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    class Config:
        orm_mode = True

class LogEntryResponse(BaseModel):
    id: int
    timestamp: datetime
    log_level: str
    source: str
    message: str
    additional_fields: dict
    class Config:
        orm_mode = True

class SearchResponse(BaseModel):
    logs: list[LogEntryResponse]
    total: int
    page: int
    per_page: int

class TimeSeriesPoint(BaseModel):
    x: str
    y: int

class SeriesData(BaseModel):
    name: str
    data: list[TimeSeriesPoint]

class DistributionItem(BaseModel):
    name: str
    value: int

class AnalyticsResponse(BaseModel):
    series: list[dict]

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication Helpers
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Log Parsing Logic
class ApacheLogParser:
    PATTERN = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(.*?)\] "(.*?)" (\d{3}) (\d+) "(.*?)" "(.*?)"'
    
    def parse(self, line: str) -> dict:
        match = re.match(self.PATTERN, line)
        if match:
            ip, timestamp_str, request, status, size, referer, user_agent = match.groups()
            timestamp = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
            log_level = 'INFO' if int(status) < 400 else 'ERROR'
            return {
                'timestamp': timestamp,
                'log_level': log_level,
                'source': 'Apache',
                'message': request,
                'additional_fields': {'ip': ip, 'status': status, 'size': size, 'referer': referer, 'user_agent': user_agent}
            }
        return None

class LogParserFactory:
    @staticmethod
    def detect_format(lines: list[str]) -> str:
        for line in lines:
            if re.match(ApacheLogParser.PATTERN, line):
                return 'apache'
        return None

    @staticmethod
    def get_parser(format: str):
        if format == 'apache':
            return ApacheLogParser()
        return None

# CRUD Operations
def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, password_hash=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_upload(db: Session, user_id: int, filename: str, size: int):
    upload = Upload(user_id=user_id, filename=filename, size=size)
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload

def bulk_insert_log_entries(db: Session, upload_id: int, log_entries: list[dict]):
    entries = [LogEntry(upload_id=upload_id, **entry) for entry in log_entries]
    db.bulk_save_objects(entries)
    db.commit()

def update_upload_status(db: Session, upload_id: int, status: str):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if upload:
        upload.status = status
        db.commit()

def search_logs(db: Session, q: str = None, log_level: str = None, start_time: datetime = None, end_time: datetime = None, source: str = None, page: int = 1, per_page: int = 20):
    query = db.query(LogEntry)
    if q:
        query = query.filter(LogEntry.message.contains(q))
    if log_level:
        query = query.filter(LogEntry.log_level == log_level)
    if start_time:
        query = query.filter(LogEntry.timestamp >= start_time)
    if end_time:
        query = query.filter(LogEntry.timestamp <= end_time)
    if source:
        query = query.filter(LogEntry.source == source)
    
    total = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()
    return {"logs": logs, "total": total, "page": page, "per_page": per_page}

def get_time_series(db: Session, start_time: datetime, end_time: datetime, interval: str):
    time_trunc = func.date_trunc(interval, LogEntry.timestamp)
    query = db.query(time_trunc.label('time'), func.count().label('count')).filter(
        LogEntry.timestamp >= start_time, LogEntry.timestamp <= end_time
    ).group_by('time').order_by('time')
    results = query.all()
    return [{"x": row.time.isoformat(), "y": row.count} for row in results]

def get_distribution(db: Session, field: str):
    group_field = getattr(LogEntry, field)
    query = db.query(group_field.label('name'), func.count().label('value')).group_by(group_field)
    results = query.all()
    return [{"name": row.name, "value": row.value} for row in results]

def get_top_errors(db: Session, n: int):
    query = db.query(LogEntry.message, func.count().label('count')).filter(
        LogEntry.log_level == 'ERROR'
    ).group_by(LogEntry.message).order_by(func.count().desc()).limit(n)
    results = query.all()
    return [{"name": row.message, "value": row.count} for row in results]

# Celery Task
@celery.task
def parse_log_file(upload_id: int, file_path: str):
    db = SessionLocal()
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        format = LogParserFactory.detect_format(lines[:10])
        if not format:
            update_upload_status(db, upload_id, 'failed')
            return
        parser = LogParserFactory.get_parser(format)
        log_entries = []
        for line in lines:
            parsed = parser.parse(line)
            if parsed:
                log_entries.append(parsed)
        bulk_insert_log_entries(db, upload_id, log_entries)
        update_upload_status(db, upload_id, 'completed')
    finally:
        db.close()
        if os.path.exists(file_path):
            os.remove(file_path)

# API Endpoints
@app.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db, user)

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/logs/upload")
async def upload_log(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.log', '.txt', '.json')):
        raise HTTPException(status_code=400, detail="Invalid file type")
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    upload = create_upload(db, current_user.id, file.filename, file.size)
    parse_log_file.delay(upload.id, file_path)
    return {"upload_id": upload.id, "status": "processing"}

@app.get("/logs/upload/{upload_id}/status")
def get_upload_status(upload_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return {"status": upload.status}

@app.get("/logs/search", response_model=SearchResponse)
def search_logs_endpoint(q: str = None, log_level: str = None, start_time: datetime = None, end_time: datetime = None, source: str = None, page: int = 1, per_page: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return search_logs(db, q, log_level, start_time, end_time, source, page, per_page)

@app.get("/analytics/time-series", response_model=AnalyticsResponse)
def get_time_series_endpoint(start_time: datetime, end_time: datetime, interval: str = "hour", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = get_time_series(db, start_time, end_time, interval)
    return {"series": [{"name": "Log Entries", "data": data}]}

@app.get("/analytics/distribution", response_model=AnalyticsResponse)
def get_distribution_endpoint(field: str = "log_level", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = get_distribution(db, field)
    return {"series": data}

@app.get("/analytics/top-errors", response_model=AnalyticsResponse)
def get_top_errors_endpoint(n: int = 10, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = get_top_errors(db, n)
    return {"series": data}
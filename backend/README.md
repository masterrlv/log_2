# Log Analyzer Backend

A FastAPI-based backend service for uploading and analyzing log files.

## Features

- User authentication (JWT)
- File upload and processing
- Log search and filtering
- Analytics and visualizations
- Background task processing with Celery
- PostgreSQL database

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis (for Celery)

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the backend directory with the following variables:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/logs_db
   SECRET_KEY=your-secret-key
   ALGORITHM=HS256
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/1
   CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
   ```
5. Create the database:
   ```bash
   createdb logs_db
   ```

## Running the Application

1. Start Redis server
2. In separate terminal windows, run:
   ```bash
   # Start Celery worker
   celery -A backend.tasks worker --loglevel=info
   
   # Start FastAPI server
   uvicorn backend.main:app --reload
   ```
3. Access the API documentation at http://localhost:8000/docs

## API Documentation

Once the server is running, you can access:
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## Project Structure

```
backend/
├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── search.py
│   │   │   └── uploads.py
│   │   └── api.py
├── config/
│   └── settings.py
├── crud/
│   ├── log_entry.py
│   ├── upload.py
│   └── user.py
├── models/
│   ├── base.py
│   ├── log_entry.py
│   ├── upload.py
│   └── user.py
├── schemas/
│   ├── log_entry.py
│   └── user.py
├── services/
│   ├── auth.py
│   ├── database.py
│   ├── log_parser.py
│   └── celery_app.py
├── tasks/
│   └── __init__.py
├── .env.example
├── main.py
└── requirements.txt
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection URL | - |
| SECRET_KEY | JWT secret key | - |
| ALGORITHM | JWT algorithm | HS256 |
| CELERY_BROKER_URL | Celery broker URL | - |
| CELERY_RESULT_BACKEND | Celery result backend | - |
| CORS_ORIGINS | Allowed CORS origins | - |

## License

MIT

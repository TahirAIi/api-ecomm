# E-Commerce Platform Backend API

This is a FastAPI-based backend for an e-commerce platform with semantic search.


## Requirements

- Python 3.12+
- PostgreSQL
- GEMNI API KEY
- DEEPSEEK API KEY
- pip

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd api-ecomm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```


3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the server is running, you can access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

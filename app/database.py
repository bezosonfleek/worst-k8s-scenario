import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Reads from env var in real deployments; falls back to local-dev default.
# In docker-compose, "postgres" is the service name, resolved via Docker's internal DNS.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://pigabid:pigabid@localhost:5432/pigabid",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, always closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

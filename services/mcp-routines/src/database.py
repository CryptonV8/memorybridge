import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Deviation: We allow sqlite fallback for local isolated testing without docker/postgres.
# In production or full CI, DATABASE_URL should be a postgres URL.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")

# For sqlite, we need to enforce foreign keys manually if we want realistic constraints
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

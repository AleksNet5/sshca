import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

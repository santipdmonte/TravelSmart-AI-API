from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
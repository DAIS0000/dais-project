import logging
import csv
import os
from fastapi import FastAPI, Depends, HTTPException, Security
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import bcrypt
import jwt
import secrets
from typing import List, Optional

# Setup logging
logging.basicConfig(filename='dais_project.log', level=logging.INFO)

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)

Base.metadata.create_all(bind=engine)

# Define RBAC
class RBAC:
    def __init__(self):
        self.permissions = {
            'admin': ['read', 'write', 'delete'],
            'editor': ['read', 'write'],
            'viewer': ['read'],
        }

    def check_permission(self, role: str, permission: str) -> bool:
        return permission in self.permissions.get(role, [])

rbac = RBAC()

# API Models
class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserResponse(BaseModel):
    username: str
    role: str

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User CRUD operations
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    user.hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    db_user = User(username=user.username, hashed_password=user.hashed_password, role=user.role)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    logging.info(f"User created: {user.username} with role {user.role}")
    return db_user

@app.get("/users/", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# RBAC enforcement
@app.get("/data/")
def read_data(role: str, permission: str, db: Session = Depends(get_db)):
    if not rbac.check_permission(role, permission):
        raise HTTPException(status_code=403, detail="Permission denied")
    logging.info(f"Access granted to {role} for {permission}")
    return {"message": "Data accessed"}

# CSV Export functionality
@app.post("/export_users/")
def export_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    with open('users.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Username", "Role"])
        for user in users:
            writer.writerow([user.id, user.username, user.role])
    logging.info("User data exported to users.csv")
    return {"message": "User data exported"}

# Main function
if __name__ == "__main__":
    import uvicorn
    os.makedirs(os.path.dirname('dais_project.log'), exist_ok=True)
    logging.info("Starting the Dais Project application")
    uvicorn.run(app, host="0.0.0.0", port=8000)
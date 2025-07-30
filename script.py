import logging
import os
import csv
import hashlib
import secrets
import jwt
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import List, Optional

logging.basicConfig(filename='dais_project.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_URL = "sqlite:///./dais_project.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

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

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

class RoleCreate(BaseModel):
    name: str

class RBAC:
    def __init__(self):
        self.permissions = {
            "admin": ["read", "write", "delete"],
            "editor": ["read", "write"],
            "viewer": ["read"],
        }

    def check_permission(self, role: str, permission: str) -> bool:
        return permission in self.permissions.get(role, [])
        
rbac_system = RBAC()

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post('/users/', response_model=UserResponse)
def create_user(user: UserCreate, db: SessionLocal = Depends(get_db)):
    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    db_user = User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        logging.error(f"User creation failed for {user.username}: user already exists.")
        raise HTTPException(status_code=400, detail="User already exists.")
    logging.info(f"User created: {user.username} with role {user.role}")
    return db_user

@app.post('/roles/', response_model=str)
def create_role(role: RoleCreate, db: SessionLocal = Depends(get_db)):
    db_role = Role(name=role.name)
    db.add(db_role)
    try:
        db.commit()
    except IntegrityError:
        logging.error(f"Role creation failed for {role.name}: role already exists.")
        raise HTTPException(status_code=400, detail="Role already exists.")
    logging.info(f"Role created: {role.name}")
    return role.name

@app.get('/users/{username}', response_model=UserResponse)
def read_user(username: str, db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        logging.error(f"User not found: {username}")
        raise HTTPException(status_code=404, detail="User not found.")
    logging.info(f"User retrieved: {username}")
    return user

@app.post('/protected-endpoint/{action}')
def protected_action(action: str, username: str, db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        logging.error(f"User not found: {username}")
        raise HTTPException(status_code=404, detail="User not found.")
    
    if not rbac_system.check_permission(user.role, action):
        logging.warn(f"User {user.username} does not have permission for action: {action}")
        raise HTTPException(status_code=403, detail="Permission denied.")
    
    logging.info(f"User {username} performed action: {action}")
    return {"message": f"Action {action} performed by {username}"}

@app.get('/export-users/')
def export_users(db: SessionLocal = Depends(get_db)):
    users = db.query(User).all()
    with open('users.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["id", "username", "role"])
        for user in users:
            writer.writerow([user.id, user.username, user.role])
    logging.info('User data exported to users.csv')
    return {"message": "User data exported successfully."}

def main():
    import uvicorn
    os.makedirs("logs", exist_ok=True)
    logging.info("Starting Dais Project with RBAC enforcement.")
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
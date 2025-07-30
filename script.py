import os
import logging
import csv
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pydantic import BaseModel
from typing import List, Dict
from cryptography.fernet import Fernet
from functools import wraps

# Setup logging
logging.basicConfig(filename='dais_project.log', level=logging.INFO)

# Database setup
DATABASE_URL = "sqlite:///./dais_project.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Role model
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    permissions = Column(String)  # Could be a JSON String of permissions


# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role")


# Create tables in the database
Base.metadata.create_all(bind=engine)


# Pydantic schemas
class UserCreate(BaseModel):
    username: str
    password: str
    role_id: int


class UserResponse(BaseModel):
    id: int
    username: str
    role: str


# RBAC decoration
def rbac_required(permission: str):
    def decorator(func):
        @wraps(func)
        def wrapper(user: User = Depends(get_current_user), *args, **kwargs):
            if permission not in user.role.permissions.split(','):
                logging.warning(f"Access denied for user {user.username} on {permission}.")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
            return func(user, *args, **kwargs)
        return wrapper
    return decorator


def get_current_user(username: str, db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# Initialize FastAPI app
app = FastAPI()


@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username, password=encrypt_password(user.password), role_id=user.role_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logging.info(f"User created: {user.username}")
    return db_user


@app.get("/users/", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    logging.info(f"Fetched users: {len(users)}")
    return users


def encrypt_password(password: str) -> str:
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    encrypted_password = cipher_suite.encrypt(password.encode())
    return encrypted_password.decode()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# CSV Export Functionality
def export_users_to_csv(db: Session):
    try:
        users = db.query(User).all()
        with open('users.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Username", "Role ID"])
            for user in users:
                writer.writerow([user.id, user.username, user.role_id])
        logging.info("Exported users to CSV successfully.")
    except Exception as e:
        logging.error(f"Error exporting users to CSV: {e}")


@app.get("/export-users/")
def export_users(db: Session = Depends(get_db)):
    export_users_to_csv(db)
    return {"message": "Users exported to CSV."}


def main():
    import uvicorn
    try:
        logging.info("Starting the Dais Project with RBAC enforcement.")
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        logging.error(f"Error starting the application: {e}")


if __name__ == "__main__":
    main()
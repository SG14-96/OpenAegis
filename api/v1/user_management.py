from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud import crud
from schema import UserModel
from db.database import SessionLocal
from models.models import User
from dependencies import get_current_user, is_super_user

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/users/", response_model=UserModel.User)
def create_user(user: UserModel.UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_super_user(current_user):
        raise HTTPException(status_code=403, detail="Operation not permitted. Only super users can create new users.")
    
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db, user)


@router.get("/users/me", response_model=UserModel.User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

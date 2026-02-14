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

@router.put("/users/{user_id}", response_model=UserModel.User)
def update_user(user_id: int, user: UserModel.UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_super_user(current_user):
        raise HTTPException(status_code=403, detail="Operation not permitted. Only super users can update users.")
    
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user(db, db_user, user)


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_super_user(current_user):
        raise HTTPException(status_code=403, detail="Operation not permitted. Only super users can delete users.")
    
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.delete_user(db, db_user)


@router.patch("/users/{user_id}/disable")
def disable_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_super_user(current_user):
        raise HTTPException(status_code=403, detail="Operation not permitted. Only super users can disable users.")
    
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.disable_user(db, db_user)
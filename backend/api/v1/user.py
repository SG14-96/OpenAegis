from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud import crud
from schema import UserModel
from models.models import User
from dependencies import get_current_user, get_db

router = APIRouter()

"""
User-related API endpoints meant for self-service operations by the authenticated user. 
These endpoints allow users to view and update their own profile information, change their password, and manage their account status (e.g., disable or delete their account). 
Each endpoint requires the user to be authenticated, ensuring that users can only access and modify their own data.
"""

@router.get("/me", response_model=UserModel.UserBase)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserModel.UserBase)
def update_me(user: UserModel.UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.update_user(db, current_user, user)


@router.put("/me/password", response_model=bool)
def update_me_password(password_update: UserModel.UserPasswordUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not crud.verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    update_result = crud.update_user_password(db, current_user, password_update.new_password)
    if not update_result:
        raise HTTPException(status_code=500, detail="Failed to update password")
    return True


@router.delete("/me")
def delete_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.delete_user(db, current_user)


@router.patch("/me/disable")
def disable_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.disable_user(db, current_user)

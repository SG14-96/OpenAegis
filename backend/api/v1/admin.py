from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud import crud
from schema import UserModel
from models.models import User
from dependencies import get_db, require_super_user

router = APIRouter()

"""
Admin-related API endpoints for managing user accounts.
These endpoints allow superusers to perform CRUD operations on user accounts, including creating new users, retrieving user information, updating user details, changing passwords, disabling accounts, and deleting accounts.
Each endpoint requires the requester to be authenticated as a superuser, ensuring that only authorized personnel can manage user accounts.
"""

@router.post("/", response_model=UserModel.User)
def create_user(user: UserModel.UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_super_user)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db, user)


@router.get("/", response_model=list[UserModel.User])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(require_super_user)):
    return crud.get_all_users(db)


@router.get("/{user_uuid}", response_model=UserModel.User)
def get_user(user_uuid: str, db: Session = Depends(get_db), current_user: User = Depends(require_super_user)):
    db_user = crud.get_user_by_uuid(db, user_uuid=user_uuid)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_uuid}", response_model=UserModel.User)
def update_user(user_uuid: str, user: UserModel.UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_super_user)):
    db_user = crud.get_user_by_uuid(db, user_uuid=user_uuid)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.isSuperUser:
        raise HTTPException(status_code=403, detail="Cannot modify another admin user.")
    return crud.update_user(db, db_user, user)


@router.put("/{user_uuid}/password", response_model=bool)
def update_user_password(user_uuid: str, password_update: UserModel.UserPasswordUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_super_user)):
    db_user = crud.get_user_by_uuid(db, user_uuid=user_uuid)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.isSuperUser:
        raise HTTPException(status_code=403, detail="Cannot modify another admin user.")
    update_result = crud.update_user_password(db, db_user, password_update.new_password)
    if not update_result:
        raise HTTPException(status_code=500, detail="Failed to update password")
    return True


@router.delete("/{user_uuid}")
def delete_user(user_uuid: str, db: Session = Depends(get_db), current_user: User = Depends(require_super_user)):
    db_user = crud.get_user_by_uuid(db, user_uuid=user_uuid)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.isSuperUser:
        raise HTTPException(status_code=403, detail="Cannot delete another admin user.")
    return crud.delete_user(db, db_user)


@router.patch("/{user_uuid}/disable")
def disable_user(user_uuid: str, db: Session = Depends(get_db), current_user: User = Depends(require_super_user)):
    db_user = crud.get_user_by_uuid(db, user_uuid=user_uuid)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.isSuperUser:
        raise HTTPException(status_code=403, detail="Cannot disable another admin user.")
    return crud.disable_user(db, db_user)

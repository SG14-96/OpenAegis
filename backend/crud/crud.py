from sqlalchemy.orm import Session

from models import models
from schema import UserModel
from auth import security
from models.models import RefreshToken
from datetime import datetime
from typing import Optional


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: UserModel.UserCreate):
    hashed = security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed,
        isSuperUser=user.isSuperUser,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not security.verify_password(password, user.hashed_password):
        return False
    return user


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_uuid(db: Session, user_uuid: str):
    return db.query(models.User).filter(models.User.user_uuid == user_uuid).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def update_user(db: Session, db_user: models.User, user_update: UserModel.UserBase):
    empty_fields = []
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_user, key, value)
        else:
            empty_fields.append(key)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"user": db_user, "empty_fields": empty_fields}


def update_user_password(db: Session, db_user: models.User, new_password: str):
    db_user.hashed_password = security.get_password_hash(new_password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, db_user: models.User):
    db.delete(db_user)
    db.commit()
    return db_user


def disable_user(db: Session, db_user: models.User):
    db_user.disabled = True
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_refresh_token(db: Session, user_id: int, token: str, expires_at: Optional[datetime] = None):
    rt = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def get_refresh_token(db: Session, token: str):
    return db.query(RefreshToken).filter(RefreshToken.token == token).first()


def revoke_refresh_token(db: Session, token: str):
    rt = get_refresh_token(db, token)
    if not rt:
        return None
    rt.revoked = True
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt

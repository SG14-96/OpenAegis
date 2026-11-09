from typing import Generator
from fastapi import Depends, HTTPException, Query, WebSocket, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from db import database
from auth import security
from crud import crud
from schema import UserModel
from models import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
# Same scheme, but yields None instead of a 401 when no token is sent — for
# public routes that reveal a bit more to signed-in users.
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = UserModel.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def get_optional_user(
    token: str | None = Depends(optional_oauth2_scheme), db: Session = Depends(get_db)
) -> models.User | None:
    """The signed-in user if a valid token was sent, otherwise None (never raises)."""
    if token is None:
        return None
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
    except JWTError:
        return None
    username = payload.get("sub")
    if username is None:
        return None
    return crud.get_user_by_username(db, username=username)

async def get_current_user_ws(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    """
    WebSocket counterpart of get_current_user.

    Native browser WebSockets can't set an Authorization header, so the access
    token travels as a query param instead (?token=...). Raising
    WebSocketException here closes the connection before the handler body
    runs — ws.accept() is never reached for an unauthenticated client.
    """
    denied = WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Could not validate credentials")
    if token is None:
        raise denied
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise denied
    except JWTError:
        raise denied
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise denied
    return user


def is_super_user(current_user: models.User):
    return current_user.isSuperUser


def require_super_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.isSuperUser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Admin access required.",
        )
    return current_user

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from crud import crud
from auth import security
from dependencies import get_db
from schema import UserModel
from jose import JWTError

router = APIRouter()


@router.post("/token", response_model=UserModel.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    # Create refresh token and persist it
    refresh_token = security.create_refresh_token(data={"sub": user.username})
    # Optionally store expiry info - decode exp claim
    try:
        decoded = security.jwt.decode(refresh_token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        exp_ts = decoded.get("exp")
        expires_at = None
        if exp_ts:
            from datetime import datetime

            expires_at = datetime.utcfromtimestamp(int(exp_ts))
    except Exception:
        expires_at = None
    # persist refresh token
    crud.create_refresh_token(db, user.id, refresh_token, expires_at)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh")
def refresh_access_token(refresh_payload: dict = Body(...), db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access token.

    Body should be: {"refresh_token": "..."}
    """
    refresh_token = refresh_payload.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing refresh_token")
    try:
        payload = security.jwt.decode(refresh_token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    token_record = crud.get_refresh_token(db, refresh_token)
    if not token_record or token_record.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked refresh token")
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(data={"sub": username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}



@router.post("/logout")
def logout_refresh_token(payload: dict = Body(...), db: Session = Depends(get_db)):
    """Revoke a refresh token. Body: {"refresh_token": "..."} """
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing refresh_token")
    rt = crud.revoke_refresh_token(db, token)
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token not found")
    return {"revoked": True}
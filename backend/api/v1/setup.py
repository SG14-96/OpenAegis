"""
First-run endpoints. Both are public: on a brand-new install there is no
one to sign in as yet.
"""
import logging
import threading

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.v1.auth import issue_token_pair
from auth import security
from dependencies import get_db, get_optional_user
from models.models import User
from onboarding.setup_code import SetupCode
from schema import UserModel
from schema.setup import FirstAdminCreate, SetupStatus

logger = logging.getLogger(__name__)

router = APIRouter()

# Serializes first-admin creation within this process; the table lock below
# covers multiple workers on Postgres.
_first_admin_lock = threading.Lock()


def _get_setup_code(request: Request) -> SetupCode:
    return request.app.state.setup_code


@router.get("/status", response_model=SetupStatus, response_model_exclude_none=True)
def get_setup_status(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    from crud.settings import get_alarm_settings

    manager = request.app.state.alarm_manager
    plugin_loaded = manager.active_plugin is not None
    return SetupStatus(
        needs_admin=db.query(User.id).first() is None,
        has_alarm=get_alarm_settings(db) is not None,
        plugin_loaded=plugin_loaded,
        plugin_error=manager.last_load_error if user is not None and not plugin_loaded else None,
    )


@router.post("/admin", response_model=UserModel.Token, status_code=status.HTTP_201_CREATED)
def create_first_admin(
    body: FirstAdminCreate,
    db: Session = Depends(get_db),
    setup_code: SetupCode = Depends(_get_setup_code),
):
    """
    Create the first administrator and sign them in. Only works while no
    users exist, and only with the setup code printed to the server log.
    """
    already_set_up = HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Setup is already complete.")

    if not setup_code.active:
        raise already_set_up
    if not setup_code.verify(body.setup_code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect setup code.")

    with _first_admin_lock:
        if db.bind.dialect.name == "postgresql":
            # Held until commit: a concurrent request blocks here, then sees
            # the new user and gets the 409 below.
            db.execute(text("LOCK TABLE users IN SHARE ROW EXCLUSIVE MODE"))
        if db.query(User.id).first() is not None:
            db.rollback()
            setup_code.consume()
            raise already_set_up

        admin = User(
            username=body.username,
            email=body.email or None,
            full_name=body.full_name or None,
            hashed_password=security.get_password_hash(body.password),
            isSuperUser=True,
            disabled=False,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        setup_code.consume()

    logger.info("First-run setup: administrator '%s' created.", admin.username)
    return issue_token_pair(db, admin)

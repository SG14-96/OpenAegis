import logging
import os
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from alarm.manager import AlarmManager
from alarm.ws_manager import WSManager
from api.v1 import auth, user, admin, alarm, hardware
from auth import security
from crud import crud
from db import database
from models.models import User
import models.settings  # noqa: F401 — register ORM models before any query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)

# ENV variables:
APP_IN_DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

app = FastAPI()

# Configure CORS
origins_env = os.getenv("FRONTEND_ORIGINS")
if origins_env:
    origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount(
    "/static/plugins",
    StaticFiles(directory=Path(__file__).parent / "plugins"),
    name="plugin_assets",
)

app.include_router(user.router, prefix="/api/v1/users", tags=["users"])
app.include_router(admin.router, prefix="/api/v1/admin/users", tags=["admin"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(alarm.router, prefix="/api/v1/alarm", tags=["alarm"])
app.include_router(hardware.router, prefix="/api/v1/hardware", tags=["hardware"])


@app.on_event("startup")
async def on_startup():
    """Run Alembic migrations, seed the initial super user, and wire the alarm subsystem."""
    try:
        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
        command.upgrade(alembic_cfg, "head")
        
        if APP_IN_DEV_MODE:
            db = database.SessionLocal()
            dev_users = [
                {"username": "admin",   "full_name": "Administrator",  "email": "admin@example.com",   "password": "admin123",   "isSuperUser": True},
                {"username": "admin2",  "full_name": "Admin Two",       "email": "admin2@example.com",  "password": "admin123",   "isSuperUser": True},
                {"username": "alice",   "full_name": "Alice Smith",     "email": "alice@example.com",   "password": "password123","isSuperUser": False},
                {"username": "bob",     "full_name": "Bob Johnson",     "email": "bob@example.com",     "password": "password123","isSuperUser": False},
                {"username": "carol",   "full_name": "Carol Williams",  "email": "carol@example.com",   "password": "password123","isSuperUser": False},
                {"username": "dave",    "full_name": "Dave Brown",      "email": "dave@example.com",    "password": "password123","isSuperUser": False},
            ]
            for u in dev_users:
                exists = db.query(User).filter(User.username == u["username"]).first()
                if not exists:
                    db.add(User(
                        username=u["username"],
                        email=u["email"],
                        full_name=u["full_name"],
                        hashed_password=security.get_password_hash(u["password"]),
                        isSuperUser=u["isSuperUser"],
                        disabled=False,
                    ))
                    print(f"Dev user '{u['username']}' created")
                else:
                    print(f"Dev user '{u['username']}' already exists")
            db.commit()
            db.close()
    except Exception as e:
        print(f"Error during startup: {e}")

    # Wire up alarm subsystem
    app.state.ws_manager = WSManager()
    app.state.alarm_manager = AlarmManager(app.state.ws_manager)

    # Restore the active plugin and alarm state from the last saved configuration.
    restore_db = database.SessionLocal()
    try:
        await app.state.alarm_manager.restore_from_config(restore_db)
    finally:
        print("Alarm state restoration complete.")
        restore_db.close()


@app.on_event("shutdown")
async def on_shutdown():
    database.engine.dispose()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
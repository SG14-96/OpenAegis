import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic.config import Config
from alembic import command

from api.v1 import auth, user, admin, alarm
from db import database
from models import models

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
app.include_router(user.router, prefix="/api/v1/users", tags=["users"])
app.include_router(admin.router, prefix="/api/v1/admin/users", tags=["admin"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(alarm.router, prefix="/api/v1/alarm", tags=["alarm"])


@app.on_event("startup")
async def on_startup():
    try:
        """Run Alembic migrations and seed the initial super user on startup."""
        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
        command.upgrade(alembic_cfg, "head")
        
        db = database.SessionLocal()
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            from crud import crud
            from schema import UserModel
            from auth import security

            admin_data = UserModel.UserCreate(
                username="admin",
                full_name="Administrator",
                email="admin@example.com",
                password="admin123"
            )
            hashed_password = security.get_password_hash(admin_data.password)
            admin_user = models.User(
                username=admin_data.username,
                email=admin_data.email,
                full_name=admin_data.full_name,
                hashed_password=hashed_password,
                isSuperUser=True,
                disabled=False
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully")
        db.close()
    except Exception as e:
        print(f"Error creating admin user: {e}")

    # Wire up alarm subsystem
    from alarm.state import AlarmState
    from alarm.ws_manager import WSManager
    from alarm.manager import AlarmManager

    app.state.alarm_state = AlarmState()
    app.state.ws_manager = WSManager()
    app.state.alarm_manager = AlarmManager(app.state.alarm_state, app.state.ws_manager)
    app.state.alarm_manager.start()


@app.on_event("shutdown")
async def on_shutdown():
    if hasattr(app.state, "alarm_manager"):
        app.state.alarm_manager.stop()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
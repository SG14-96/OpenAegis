import uvicorn
from fastapi import FastAPI

from api.v1 import auth, user_management
from db import database
from models import models

app = FastAPI()
app.include_router(user_management.router, prefix="/api/v1/user_management", tags=["user_management"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


@app.on_event("startup")
def on_startup():
    database.Base.metadata.create_all(bind=database.engine)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
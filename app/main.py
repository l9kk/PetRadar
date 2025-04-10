from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import json
from datetime import datetime
from uuid import UUID

from app.api.routes import api_router
from app.core.config import settings
from app.core.database import get_db, Base, engine

Base.metadata.create_all(bind=engine)


# Custom JSON encoder to handle UUID and datetime
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


app = FastAPI(
    title=settings.APP_NAME, json_encoder=CustomJSONEncoder  # Use our custom encoder
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME} API"}


if __name__ == "__main__":
    import uvicorn
    import os

    try:
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run("app.main:app", host="0.0.0.0", port=port)
    except ValueError as e:
        print(f"Error parsing PORT value: {os.environ.get('PORT')}")
        print(f"Using default port 8000 instead")
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000)

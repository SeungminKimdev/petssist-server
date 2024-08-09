from fastapi import FastAPI
from database import engine, Base
import models
from routers import router as api_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(api_router)
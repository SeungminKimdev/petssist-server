from fastapi import FastAPI, HTTPException
from database import engine, Base
import models
from fastapi.middleware.cors import CORSMiddleware
from routers import router as api_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def main():
    return {"message":"Connected"}
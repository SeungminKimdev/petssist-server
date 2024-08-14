from fastapi import APIRouter
from routers import users, dogs

router = APIRouter()
router.include_router(users.router, tags=['users'])
router.include_router(dogs.router, tags=['dogs'])
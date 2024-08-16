from fastapi import APIRouter
from routers import users, dogs, webSocket

router = APIRouter()
router.include_router(users.router, tags=['users'])
router.include_router(dogs.router, tags=['dogs'])
router.include_router(webSocket.router, tags=['webSocket'])
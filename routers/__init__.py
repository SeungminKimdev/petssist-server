from fastapi import APIRouter
from . import test

router = APIRouter()
router.include_router(test.router, tags=['test'])
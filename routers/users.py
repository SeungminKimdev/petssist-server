import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from core.security import create_access_token, get_password_hash, create_refresh_token
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserCreateRequest, UserCreate, RefreshTokenCreate
from crud import create_user, crud_create_refresh_token

router = APIRouter()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 회원가입 기능
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: Request, db: Session = Depends(get_db)):
    try:
        user_data = await request.json()
        user = UserCreateRequest(**user_data)
    except ValidationError as e:
        error_messages = e.errors()
        errors = [item['loc'][0] for item in error_messages]
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"errorMessage": f"{errors} is a required field."}
        )
    
    try:
        user_data = UserCreate(
            loginId=user.loginId,
            password=get_password_hash(user.password),
            name=user.name,
        )
        db_user = create_user(db, user_data)
        
        # 리프레시 토큰 생성 및 저장
        refresh_token_str = create_refresh_token(data={"sub": db_user.loginId})
        refresh_token_data = RefreshTokenCreate(
            token=refresh_token_str,
            createdAt=datetime.utcnow(),
            expiresAt=datetime.utcnow() + timedelta(days=7)  # 리프레시 토큰 만료 시간 설정
        )
        crud_create_refresh_token(db, refresh_token_data, db_user.id)
        
        access_token = create_access_token(data={"sub": db_user.loginId})
        headers = {"accessToken": access_token}
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": "User created successfully"},
            headers=headers
        )
    except Exception as e:
        logger.error(f"Error occurred while creating user: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"errorMessage": "Server error"},
        )
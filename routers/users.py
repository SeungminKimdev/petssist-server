import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request, status, Query, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from core.security import create_access_token, get_password_hash, create_refresh_token, verify_password, decode_access_token
from core.security import REFRESH_TOKEN_EXPIRE_DAYS
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserCreateRequest, UserCreate, RefreshTokenCreate
from crud import create_user, crud_create_refresh_token, get_user_by_loginId, get_refresh_token_by_user, delete_refresh_token
from routers.auth import verify_and_refresh_token

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
            content={"errorMessage": f"{errors} is a required field"}
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
            expiresAt=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
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

# loginId 중복 확인 기능
@router.get("/check-loginid", status_code=status.HTTP_200_OK)
async def check_loginid(loginid: str = Query(...), db: Session = Depends(get_db)):
    if not loginid.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"errorMessage": "Loginid cannot be null or empty"}
        )

    try:
        existing_user = get_user_by_loginId(db, loginid)
        if existing_user:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"errorMessage": "Loginid is already in use"}
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Loginid is available"}
        )

    except Exception as e:
        logger.error(f"Error occurred while creating user: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"errorMessage": "Server error"}
        )

# 로그인 기능
@router.post("/login", status_code=status.HTTP_200_OK)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        loginData = await request.json()
        loginId = loginData.get("loginId")
        password = loginData.get("password")

        # 사용자가 존재하는지 확인
        dbUser = get_user_by_loginId(db, loginId)
        if not dbUser:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"errorMessage": "LoginId does not exist"}
            )

        # 비밀번호 확인
        if not verify_password(password, dbUser.password):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"errorMessage": "Password is incorrect"}
            )
        
        # 잔여 리프레시 토큰 삭제
        existing_refresh_token = get_refresh_token_by_user(db, dbUser.id)
        if existing_refresh_token:
            delete_refresh_token(db, existing_refresh_token.id)

        accessToken = create_access_token(data={"sub": dbUser.loginId})
        refreshTokenStr = create_refresh_token(data={"sub": dbUser.loginId})
        refreshTokenData = RefreshTokenCreate(
            token=refreshTokenStr,
            createdAt=datetime.utcnow(),
            expiresAt=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        crud_create_refresh_token(db, refreshTokenData, dbUser.id)

        headers = {"accessToken": accessToken}
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Login successfully"},
            headers=headers
        )

    except Exception as e:
        logger.error(f"Error occurred while logging in: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"errorMessage": "Server error"}
        )

#유저 정보 조회 기능
@router.get("/users/me", status_code=status.HTTP_200_OK)
async def get_user_info(accessToken: str = Header(...), db: Session = Depends(get_db)):
    is_valid, result = verify_and_refresh_token(db, accessToken)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"errorMessage": result}
        )
    try:
        payload = decode_access_token(result)
        loginId = payload.get("sub")
        db_user = get_user_by_loginId(db, loginId)
        if not db_user:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"errorMessage": "Server error"}
            )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "loginId": db_user.loginId,
                "name": db_user.name
            },
            headers={"accessToken": result}
        )
    except:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"errorMessage": "Server error"}
        )
from fastapi import APIRouter, HTTPException, Depends, Request, status, Header, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import verify_and_refresh_token, decode_access_token
from crud import create_dog, get_user_by_loginId
from schemas import DogCreate
import logging
from pydantic import ValidationError

router = APIRouter()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/dogs", status_code=status.HTTP_201_CREATED)
async def add_dog(request: Request, accessToken: str = Header(...), db: Session = Depends(get_db)):
    # 토큰 검증
    is_valid, result = verify_and_refresh_token(db, accessToken)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"errorMessage": result}
        )

    try:
        user_data = await request.json()
        try:
            dog = DogCreate(**user_data)
        except ValidationError as e:
            error_messages = e.errors()
            errors = [item['loc'][0] for item in error_messages]
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"errorMessage": f"{errors} is a required field"}
            )

        payload = decode_access_token(result)
        loginId = payload.get("sub")
        db_user = get_user_by_loginId(db, loginId)
        if not db_user:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"errorMessage": "Server error"}
            )
        
        # 강아지 정보 생성
        db_dog = create_dog(db, dog, db_user.id)
        if db_dog:
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={"message": "Dog information added successfully"}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"errorMessage": "Server error"}
            )
    except Exception as e:
        logger.error(f"Error adding dog: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"errorMessage": "Server error"}
        )
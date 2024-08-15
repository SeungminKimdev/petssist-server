from datetime import datetime, timedelta
from typing import Optional, Dict, Union, Tuple
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from core.security import create_access_token, decode_access_token, decode_refresh_token
from crud import get_refresh_token, delete_refresh_token, get_refresh_token_by_user, get_user_by_loginId
from fastapi.responses import JSONResponse

def verify_and_refresh_token(db: Session, access_token: str) -> Tuple[bool, Union[str, None]]:
    try:
        # Access Token 검증
        payload = decode_access_token(access_token)
        if payload:
            return (True, access_token)  # 유효한 액세스 토큰

    except JWTError:
        # Access Token이 만료되었거나 유효하지 않음
        pass

    # Access Token에서 사용자 ID 추출
    try:
        payload = decode_access_token(access_token)
        if not payload:
            return (False, "Invalid access token")
        loginId = payload.get("sub")
        if not loginId:
            return (False, "Invalid access token") # access token에 sub이 없음

        # 사용자 ID로 Refresh Token 조회
        userId = get_user_by_loginId(db, loginId).id
        db_refresh_token = get_refresh_token_by_user(db, userId)
        if not db_refresh_token:
            return (False, "Refresh token not found")

        # Refresh Token 검증
        refresh_payload = decode_refresh_token(db_refresh_token.token)
        if not refresh_payload:
            delete_refresh_token(db, db_refresh_token.id)  # 유효하지 않은 Refresh Token 삭제
            return (False, "Invalid refresh token")

        # Refresh Token이 유효한 경우 새로운 Access Token 발급
        new_access_token = create_access_token(data={"sub": loginId})
        return (True, new_access_token)

    except JWTError:
        return (False, "Invalid access token")
from fastapi import APIRouter, HTTPException, Depends, Request, status, Header, Body, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import verify_and_refresh_token, decode_access_token
from crud import create_dog, get_user_by_loginId, create_picture, get_pictures_by_dog, get_dog_by_user
from schemas import DogCreate, PictureCreate
import logging
from pydantic import ValidationError
import shutil
import os

router = APIRouter()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 강아지 정보 등록
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
                content={"message": "Dog information added successfully"},
                headers={"accessToken": result}
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

# 강아지 사진 업로드
@router.post("/dogs/photos", status_code=status.HTTP_201_CREATED)
async def upload_dog_photo(accessToken: str = Header(...), db: Session = Depends(get_db), image: UploadFile = File(...)):
    # 토큰 검증
    is_valid, result = verify_and_refresh_token(db, accessToken)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"errorMessage": result}
        )

    try:
        # Access Token에서 로그인 ID 추출
        payload = decode_access_token(result)
        loginId = payload.get("sub")
        db_user = get_user_by_loginId(db, loginId)
        if not db_user:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"errorMessage": "Server error"}
            )
            
        dog = get_dog_by_user(db, db_user.id)
        if not dog:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"errorMessage": "Dog information does not exist"}
            )
        # 기존 사진이 있는지 확인
        existing_photo = get_pictures_by_dog(db, dog.id)
        if existing_photo:
            # 기존 파일 삭제
            if os.path.exists(existing_photo.photoPath):
                os.remove(existing_photo.photoPath)

            # 새 파일 경로 생성
            photo_path = f"photos/{db_user.name}_profile"
            with open(photo_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            # 기존 사진 정보 업데이트
            existing_photo.fileName = image.filename
            existing_photo.contentType = image.content_type
            existing_photo.photoPath = photo_path
            db.commit()

        else:
            # 사진 정보 데이터베이스에 저장 (새 사진)
            photo_path = f"photos/{db_user.name}_profile"
            with open(photo_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            photo_data = PictureCreate(
                fileName=image.filename,
                contentType=image.content_type,
                photoPath=photo_path
            )
            logger.warning(f"{dog.id}")
            create_picture(db, photo_data, dog.id)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": "Photo upload completed"},
            headers={"accessToken": result}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"errorMessage": "Server error"}
        )

# 강아지 정보 수정
@router.put("/dogs/me", status_code=status.HTTP_200_OK)
async def update_dog_info(
    accessToken: str = Header(...),
    db: Session = Depends(get_db),
    dogName: str = Body(...),
    breed: str = Body(...),
    breedCategory: int = Body(...),
    dogAge: int = Body(...),
    sex: str = Body(...),
    weight: float = Body(...)
):
    # 토큰 검증
    is_valid, result = verify_and_refresh_token(db, accessToken)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"errorMessage": result}
        )

    try:
        # Access Token에서 로그인 ID 추출
        payload = decode_access_token(result)
        loginId = payload.get("sub")
        db_user = get_user_by_loginId(db, loginId)
        if not db_user:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"errorMessage": "Server error"}
            )
        
        # 사용자의 강아지 정보 조회
        dog = get_dog_by_user(db, db_user.id)
        if not dog:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"errorMessage": "Dog information does not exist"}
            )

        # 강아지 정보 업데이트
        dog.dogName = dogName
        dog.breed = breed
        dog.breedCategory = breedCategory
        dog.dogAge = dogAge
        dog.sex = sex
        dog.weight = weight

        db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Dog information change successfully"},
            headers={"accessToken": result}
        )

    except ValidationError as e:
        error_messages = e.errors()
        errors = [item['loc'][0] for item in error_messages]
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"errorMessage": f"{errors} is a required field"}
        )
    except Exception as e:
        logger.error(f"Error updating dog: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"errorMessage": "Server error"}
        )

# 강아지 정보 조회
@router.get("/dogs/me", status_code=status.HTTP_200_OK)
async def get_dog_info(accessToken: str = Header(...), db: Session = Depends(get_db)):
    # 토큰 검증
    is_valid, result = verify_and_refresh_token(db, accessToken)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"errorMessage": "Invalid token"}
        )

    try:
        # Access Token에서 로그인 ID 추출
        payload = decode_access_token(result)
        loginId = payload.get("sub")
        db_user = get_user_by_loginId(db, loginId)
        if not db_user:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"errorMessage": "Server error"}
            )
        
        # 사용자의 강아지 정보 조회
        dog = get_dog_by_user(db, db_user.id)
        if not dog:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"errorMessage": "Dog information does not exist"}
            )

        # 성공 시 강아지 정보 반환
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "dogName": dog.dogName,
                "breed": dog.breed,
                "breedCategory": dog.breedCategory,
                "dogAge": dog.dogAge,
                "sex": dog.sex,
                "weight": dog.weight
            },
            headers={"accessToken": result}
        )

    except Exception as e:
        logger.error(f"Error fetching dog information: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"errorMessage": "Server error"}
        )

# 강아지 사진 가져오기
@router.get("/dogs/photos", response_class=FileResponse)
async def get_dog_photo(accessToken: str = Header(...), db: Session = Depends(get_db)):
    # 토큰 검증
    is_valid, result = verify_and_refresh_token(db, accessToken)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"errorMessage": result}
        )

    try:
        # Access Token에서 로그인 ID 추출
        payload = decode_access_token(result)
        loginId = payload.get("sub")
        db_user = get_user_by_loginId(db, loginId)
        if not db_user:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"errorMessage": "Server error"}
            )
            
        dog = get_dog_by_user(db, db_user.id)
        if not dog:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"errorMessage": "Dog information does not exist"}
            )
        
        # 사진 정보 가져오기
        existing_photo = get_pictures_by_dog(db, dog.id)
        if not existing_photo or not os.path.exists(existing_photo.photoPath):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"errorMessage": "Photo not found"}
            )

        # 사진 파일 반환
        headers = {"accessToken": result}
        return FileResponse(path=existing_photo.photoPath, media_type=existing_photo.contentType, headers=headers)

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"errorMessage": "Server error"}
        )
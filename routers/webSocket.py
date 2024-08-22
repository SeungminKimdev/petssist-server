from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from core.security import decode_access_token
from database import get_db
from routers.auth import verify_and_refresh_token
from schemas import SenseDataCreate
from crud import create_sense_data, get_user_by_loginId, get_dog_by_user, get_dog_weight_by_user
from models import Sequence, Bcgdata
import json

router = APIRouter()

sensorDataBuffer = []
bufferSize = 0

# 모델 함수 - 동욱님 코드
async def run_first_model(db, dogId, websocket, input_data):
    # 모델 로직
    # 모델 함수 (수면 중일 때 실행) - 예인님 코드
    async def run_second_model(input_data):
        # PyTorch 모델 로직
        return True
    
    sequenceData = Sequence()
    bcgData = Bcgdata()
    if bool(sequenceData.heartAnomoly): # 심박 이상치 발견
        bcgHeart = [{"time": bcg.time, "heart": bcg.heart} for bcg in bcgData]
    else:
        bcgHeart = []
    # sequence 데이터와 bcg 데이터를 클라이언트로 전송
    await websocket.send_json({"heartRate": sequenceData.heartRate,
                               "respirationRate":sequenceData.respirationRate,
                               "heartAnomoly":bool(sequenceData.heartAnomoly),
                               "senseData":bcgHeart
                              })
    return



# 센서 데이터를 데이터베이스에 저장
async def upload_sense_data(db, dog_id, sense_data_list):
    for sense_data in sense_data_list:
        sensor_data_obj = SenseDataCreate(
                measureTime=sense_data["time"],
                ax=sense_data["ax"],
                ay=sense_data["ay"],
                az=sense_data["az"],
                bcg=sense_data["bcg"],
                gx=sense_data["gx"],
                gy=sense_data["gy"],
                gz=sense_data["gz"],
                temperature=sense_data["temperature"]
            )
        create_sense_data(db, sensor_data_obj, dog_id)

@router.websocket("/wsbt")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    
    try:
        # 첫 번째 메시지에서 액세스 토큰을 수신
        data = await websocket.receive_json()
        accessToken = data.get("accessToken")

        # 토큰 검증
        is_valid, result = verify_and_refresh_token(db, accessToken)
        if not is_valid:
            await websocket.send_json({"auth_success": False, "message": "Authentication fail", "accessToken": result})
            await websocket.close()
            return
        else:
            await websocket.send_json({"auth_success": True, "message": "Authentication success", "accessToken": result})

        payload = decode_access_token(result)
        
        # 사용자 정보에서 강아지 정보 조회
        loginId = payload.get("sub")
        db_user = get_user_by_loginId(db, loginId)
        dog = get_dog_by_user(db, db_user.id)
        if not dog:
            await websocket.send_json({"auth_success": False, "message": "Dog information does not exist", "accessToken": result})
            await websocket.close()
            return
        
        # 인증 후 수신된 데이터 처리
        while True:
            data = await websocket.receive_json()
            sensor_data_list = data.get("senserData")

            if not sensor_data_list:
                continue
            await upload_sense_data(db, dog.id, sensor_data_list)
            sensorDataBuffer.extend(sensor_data_list)
            bufferSize += 7
            if bufferSize >= 560:
                modelInputData = sensorDataBuffer[:560]

                # 모델 실행
                await run_first_model(db, dog.id, websocket, modelInputData)

                # 데이터 버퍼 갱신
                sensorDataBuffer = sensorDataBuffer[280:]
                bufferSize -= 280

    except WebSocketDisconnect:
        print("Client disconnected")
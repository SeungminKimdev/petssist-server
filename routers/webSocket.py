from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from core.security import decode_access_token
from database import get_db
from routers.auth import verify_and_refresh_token
from schemas import SenseDataCreate
from crud import create_sense_data, get_user_by_loginId, get_dog_by_user
import json

router = APIRouter()

@router.websocket("/wsbt")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    
    try:
        # 첫 번째 메시지에서 액세스 토큰을 수신
        data = await websocket.receive_json()
        accessToken = data.get("accesstoken")

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

            # 센서 데이터를 데이터베이스에 저장
            for sensor_data in sensor_data_list:
                sensor_data_obj = SenseDataCreate(
                    measureTime=sensor_data["time"],
                    ax=sensor_data["ax"],
                    ay=sensor_data["ay"],
                    az=sensor_data["az"],
                    bcg=sensor_data["bcg"],
                    gx=sensor_data["gx"],
                    gy=sensor_data["gy"],
                    gz=sensor_data["gz"],
                    temperature=sensor_data["temperature"],
                )
                create_sense_data(db, sensor_data_obj, dog.id)

            # 센서 데이터 처리 (여기서 임의로 데이터를 생성하여 반환)
            

            # 응답 전송
            await websocket.send_json({"message": "Data received successfully"})

    except WebSocketDisconnect:
        print("Client disconnected")
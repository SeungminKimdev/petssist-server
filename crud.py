from sqlalchemy.orm import Session
import models, schemas
from sqlalchemy.exc import SQLAlchemyError

# User CRUD
def get_user(db: Session, user_id: int) -> models.User:
    try:
        return db.query(models.User).filter(models.User.id == user_id).first()
    except SQLAlchemyError as e:
        raise Exception(f"Database error: {str(e)}")

def get_user_by_loginId(db: Session, loginId: str) -> models.User:
    try:
        return db.query(models.User).filter(models.User.loginId == loginId).first()
    except SQLAlchemyError as e:
        raise Exception(f"Database error: {str(e)}")

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(loginId=user.loginId, password=user.password, name=user.name)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")

# Dog CRUD
def get_dog(db: Session, dog_id: int) -> models.Dog:
    try:
        return db.query(models.Dog).filter(models.Dog.id == dog_id).first()
    except SQLAlchemyError as e:
        raise Exception(f"Database error: {str(e)}")

def create_dog(db: Session, dog: schemas.DogCreate, user_id: int) -> models.Dog:
    db_dog = models.Dog(**dog.dict(), userId=user_id)
    try:
        db.add(db_dog)
        db.commit()
        db.refresh(db_dog)
        return db_dog
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")

def get_dog_by_user(db: Session, user_id: int) -> list[models.Dog]:
    try:
        return db.query(models.Dog).filter(models.Dog.userId == user_id).first()
    except SQLAlchemyError as e:
        raise Exception(f"Database error: {str(e)}")

# Picture CRUD
def create_picture(db: Session, picture: schemas.PictureCreate, dog_id: int) -> models.Picture:
    db_picture = models.Picture(**picture.dict(), dogId=dog_id)
    try:
        db.add(db_picture)
        db.commit()
        db.refresh(db_picture)
        return db_picture
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")

def get_pictures_by_dog(db: Session, dog_id: int) -> list[models.Picture]:
    try:
        return db.query(models.Picture).filter(models.Picture.dogId == dog_id).first()
    except SQLAlchemyError as e:
        raise Exception(f"Database error: {str(e)}")

# SenseData CRUD
def create_sense_data(db: Session, sense_data: schemas.SenseDataCreate, dog_id: int, device_id: int) -> models.SenseData:
    db_sense_data = models.SenseData(**sense_data.dict(), dogId=dog_id, deviceId=device_id)
    try:
        db.add(db_sense_data)
        db.commit()
        db.refresh(db_sense_data)
        return db_sense_data
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")

def get_sense_data_by_dog(db: Session, dog_id: int) -> list[models.SenseData]:
    try:
        return db.query(models.SenseData).filter(models.SenseData.dogId == dog_id).all()
    except SQLAlchemyError as e:
        raise Exception(f"Database error: {str(e)}")

# Device CRUD
def get_device(db: Session, device_id: int) -> models.Device:
    try:
        return db.query(models.Device).filter(models.Device.id == device_id).first()
    except SQLAlchemyError as e:
        raise Exception(f"Database error: {str(e)}")

def create_device(db: Session, device: schemas.DeviceCreate) -> models.Device:
    db_device = models.Device(name=device.name)
    try:
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        return db_device
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")

# Connected CRUD
def create_connected(db: Session, connected: schemas.ConnectedCreate) -> models.Connected:
    db_connected = models.Connected(**connected.dict())
    try:
        db.add(db_connected)
        db.commit()
        db.refresh(db_connected)
        return db_connected
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")

def get_connected_by_user(db: Session, user_id: int) -> list[models.Connected]:
    try:
        return db.query(models.Connected).filter(models.Connected.userId == user_id).all()
    except SQLAlchemyError as e:
        raise Exception(f"Database error: {str(e)}")

# RefreshToken CRUD
def crud_create_refresh_token(db: Session, token: schemas.RefreshTokenCreate, user_id: int) -> models.RefreshToken:
    db_token = models.RefreshToken(**token.dict(), userId=user_id)
    try:
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")

def get_refresh_token(db: Session, token_id: int) -> models.RefreshToken:
    try:
        return db.query(models.RefreshToken).filter(models.RefreshToken.id == token_id).first()
    except SQLAlchemyError as e:
        raise Exception(f"Database error: {str(e)}")

def delete_refresh_token(db: Session, token_id: int) -> None:
    try:
        db.query(models.RefreshToken).filter(models.RefreshToken.id == token_id).delete()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")
    
def get_refresh_token_by_user(db: Session, user_id: int) -> models.RefreshToken:
    try:
        return db.query(models.RefreshToken).filter(models.RefreshToken.userId == user_id).first()
    except SQLAlchemyError as e:
        raise Exception(f"Database error: {str(e)}")
from sqlalchemy.orm import Session
from . import models, schemas

# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_loginId(db: Session, loginId: str):
    return db.query(models.User).filter(models.User.loginId == loginId).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(loginId=user.loginId, password=user.password, name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Dog CRUD
def get_dog(db: Session, dog_id: int):
    return db.query(models.Dog).filter(models.Dog.id == dog_id).first()

def create_dog(db: Session, dog: schemas.DogCreate, user_id: int):
    db_dog = models.Dog(**dog.dict(), userId=user_id)
    db.add(db_dog)
    db.commit()
    db.refresh(db_dog)
    return db_dog

def get_dogs_by_user(db: Session, user_id: int):
    return db.query(models.Dog).filter(models.Dog.userId == user_id).all()

# Picture CRUD
def create_picture(db: Session, picture: schemas.PictureCreate, dog_id: int):
    db_picture = models.Picture(**picture.dict(), dogId=dog_id)
    db.add(db_picture)
    db.commit()
    db.refresh(db_picture)
    return db_picture

def get_pictures_by_dog(db: Session, dog_id: int):
    return db.query(models.Picture).filter(models.Picture.dogId == dog_id).all()

# SenseData CRUD
def create_sense_data(db: Session, sense_data: schemas.SenseDataCreate, dog_id: int, device_id: int):
    db_sense_data = models.SenseData(**sense_data.dict(), dogId=dog_id, deviceId=device_id)
    db.add(db_sense_data)
    db.commit()
    db.refresh(db_sense_data)
    return db_sense_data

def get_sense_data_by_dog(db: Session, dog_id: int):
    return db.query(models.SenseData).filter(models.SenseData.dogId == dog_id).all()

# Device CRUD
def get_device(db: Session, device_id: int):
    return db.query(models.Device).filter(models.Device.id == device_id).first()

def create_device(db: Session, device: schemas.DeviceCreate):
    db_device = models.Device(name=device.name)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

# Connected CRUD
def create_connected(db: Session, connected: schemas.ConnectedCreate):
    db_connected = models.Connected(**connected.dict())
    db.add(db_connected)
    db.commit()
    db.refresh(db_connected)
    return db_connected

def get_connected_by_user(db: Session, user_id: int):
    return db.query(models.Connected).filter(models.Connected.userId == user_id).all()

# RefreshToken CRUD
def create_refresh_token(db: Session, token: schemas.RefreshTokenCreate, user_id: int):
    db_token = models.RefreshToken(**token.dict(), userId=user_id)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def get_refresh_token(db: Session, token_id: int):
    return db.query(models.RefreshToken).filter(models.RefreshToken.id == token_id).first()
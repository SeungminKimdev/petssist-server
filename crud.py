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

def get_dog_weight_by_user(db: Session, user_id: int) -> list[float]:
    try:
        return db.query(models.Dog.weight).filter(models.Dog.userId == user_id).all()
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
def create_sense_data(db: Session, sense_data: schemas.SenseDataCreate, dog_id: int) -> models.SenseData:
    db_sense_data = models.SenseData(**sense_data.dict(), dogId=dog_id)
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

# Sequence CRUD
def create_sequence(db: Session, sequence: schemas.SequenceCreate) -> models.Sequence:
    db_sequence = models.Sequence(**sequence.dict())
    db.add(db_sequence)
    db.commit()
    db.refresh(db_sequence)
    return db_sequence

def get_sequence(db: Session, sequence_id: int) -> models.Sequence:
    return db.query(models.Sequence).filter(models.Sequence.id == sequence_id).first()

def get_sequences_by_dog(db: Session, dog_id: int) -> list[models.Sequence]:
    return db.query(models.Sequence).filter(models.Sequence.dogId == dog_id).all()

# Bcgdata CRUD
def create_bcgdata(db: Session, bcgdata: schemas.BcgdataCreate) -> models.Bcgdata:
    db_bcgdata = models.Bcgdata(**bcgdata.dict())
    db.add(db_bcgdata)
    db.commit()
    db.refresh(db_bcgdata)
    return db_bcgdata

def get_bcgdata_by_sequence(db: Session, sequence_id: int) -> list[models.Bcgdata]:
    return db.query(models.Bcgdata).filter(models.Bcgdata.sequenceId == sequence_id).all()

# TargetExercise CRUD
def create_target_exercise(db: Session, target_exercise: schemas.TargetExerciseCreate) -> models.TargetExercise:
    db_target_exercise = models.TargetExercise(**target_exercise.dict())
    db.add(db_target_exercise)
    db.commit()
    db.refresh(db_target_exercise)
    return db_target_exercise

def get_target_exercise(db: Session, dog_id: int) -> models.TargetExercise:
    return db.query(models.TargetExercise).filter(models.TargetExercise.dogId == dog_id).first()

def update_target_exercise(db: Session, dog_id: int, today: int) -> models.TargetExercise:
    target_exercise = get_target_exercise(db, dog_id)
    if target_exercise:
        target_exercise.today = today
        db.commit()
        db.refresh(target_exercise)
    return target_exercise
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship

from database import Base

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    loginId = Column(String(30), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(30), nullable=False)
    
    dogs = relationship('Dog', back_populates='user')
    tokens = relationship('RefreshToken', back_populates='user')

class Dog(Base):
    __tablename__ = 'dog'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.id'))
    dogName = Column(String(255), nullable=False)
    breed = Column(String(255), nullable=False)
    breedCategory = Column(Integer, nullable=False)
    dogAge = Column(Integer, nullable=False)
    sex = Column(String(20), nullable=False)
    weight = Column(Float, nullable=False)
    
    user = relationship('User', back_populates='dogs')
    pictures = relationship('Picture', back_populates='dog')
    senseDatas = relationship('SenseData', back_populates='dog')

class Picture(Base):
    __tablename__ = 'picture'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dogId = Column(Integer, ForeignKey('dog.id'))
    fileName = Column(String(255), nullable=False)
    contentType = Column(String(128), nullable=False)
    photoPath = Column(String(255), nullable=False)

    dog = relationship('Dog', back_populates='pictures')

class SenseData(Base):
    __tablename__ = 'senseData'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dogId = Column(Integer, ForeignKey('dog.id'))
    measureTime = Column(DateTime(timezone=True), nullable=False)
    ax = Column(Integer, nullable=False)
    ay = Column(Integer, nullable=False)
    az = Column(Integer, nullable=False)
    bcg = Column(Integer, nullable=False)
    gx = Column(Integer, nullable=False)
    gy = Column(Integer, nullable=False)
    gz = Column(Integer, nullable=False)
    temperature = Column(Float, nullable=False)

    dog = relationship('Dog', back_populates='senseDatas')

class RefreshToken(Base):
    __tablename__ = 'refreshToken'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.id'))
    token = Column(String(500), nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False)
    expiresAt = Column(DateTime(timezone=True), nullable=False)

    user = relationship('User', back_populates='tokens')
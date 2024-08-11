from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship

from database import Base

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    loginId = Column(String(30), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(30), unique=True, nullable=False)
    
    dogs = relationship('Dog', back_populates='userId')
    connects = relationship('Connected', back_populates='userId')
    tokens = relationship('RefreshToken', back_populates='userId')

class Dog(Base):
    __tablename__ = 'dog'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.id'))
    dogName = Column(String(255), nullable=False)
    breed = Column(String(255), nullable=False)
    dogAge = Column(Integer, nullable=False)
    sex = Column(String(20), nullable=False)
    weight = Column(Float, nullable=False)
    
    pictures = relationship('Picture', back_populates='dogId')
    senseDatas = relationship('SenseData', back_populates='dogId')

class Picture(Base):
    __tablename__ = 'picture'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dogId = Column(Integer, ForeignKey('dog.id'))
    fileName = Column(String(255), nullable=False)
    contentType = Column(String(128), nullable=False)
    photoPath = Column(String(255), nullable=False)

class SenseData(Base):
    __tablename__ = 'senseData'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dogId = Column(Integer, ForeignKey('dog.id'))
    deviceId = Column(Integer, ForeignKey('device.id'))
    measureTime = Column(DateTime(timezone=True), nullable=False)
    ax = Column(Integer, nullable=False)
    ay = Column(Integer, nullable=False)
    az = Column(Integer, nullable=False)
    bcg = Column(Integer, nullable=False)
    gx = Column(Integer, nullable=False)
    gy = Column(Integer, nullable=False)
    gz = Column(Integer, nullable=False)
    temperature = Column(Float, nullable=False)

class Device(Base):
    __tablename__ = 'device'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    
    datas = relationship('SenseData', back_populates='deviceId')
    connects = relationship('Connected', back_populates='deviceId')

class Connected(Base):
    __tablename__ = 'connected'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.id'))
    deviceId = Column(Integer, ForeignKey('device.id'))
    connectTime = Column(DateTime(timezone=True), nullable=False)

class RefreshToken(Base):
    __tablename__ = 'refreshToken'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.id'))
    token = Column(String(500), nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False)
    expiresAt = Column(DateTime(timezone=True), nullable=False)
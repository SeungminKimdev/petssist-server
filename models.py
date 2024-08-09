from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    loginId = Column(String(30), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(30), unique=True, nullable=False)
    
    dogs = relationship('Dog', back_populates='userId')

class Dog(Base):
    __tablename__ = 'dog'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.id'))
    dogName = Column(String(255), nullable=False)
    breed = Column(String(255), nullable=False)
    dogAge = Column(Integer, nullable=False)
    sex = Column(String(20), nullable=False)
    
    pictures = relationship('Picture', back_populates='dogId')

class Picture(Base):
    __tablename__ = 'picture'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dogId = Column(Integer, ForeignKey('Dog.id'))
    fileName = Column(String(255), nullable=False)
    contentType = Column(String(128), nullable=False)
    photoPath = Column(String(255), nullable=False)
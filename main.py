from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from db.database import *
from settings.security import *
from config.dependencies import *
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Запуск приложения
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app="main:app", reload=True)

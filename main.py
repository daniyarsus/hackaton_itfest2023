from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import jwt
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все домены (это можно настроить на конкретные домены в production)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все HTTP-методы
    allow_headers=["*"],  # Разрешить все заголовки
)

DATABASE_URL = "sqlite:///./test.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="student")


Base.metadata.create_all(bind=engine)


class UserIn(BaseModel):
    username: str
    password: str


class UserInRegistration(BaseModel):
    username: str
    email: str
    password: str


SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Неверные учетные данные")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    session = SessionLocal()
    user = session.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    return user


@app.post("/register")
async def register(user_in: UserInRegistration):
    session = SessionLocal()
    user = User(username=user_in.username, email=user_in.email, password=user_in.password)
    session.add(user)
    session.commit()
    return {"username": user.username, "email": user.email}


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    session = SessionLocal()

    # Аутентификация с использованием имени пользователя или электронной почты
    user = session.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()

    if not user or user.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

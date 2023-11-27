from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import jwt
from datetime import datetime, timedelta

app = FastAPI()
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
    group = Column(Integer, default="")  # Добавлено новое поле
    course = Column(Integer, default="")  # Добавлено новое поле
    first_name = Column(String, default="")  # Добавлено новое поле
    last_name = Column(String, default="")  # Добавлено новое поле

Base.metadata.create_all(bind=engine)


class UserIn(BaseModel):
    username: str
    password: str


class UserInRegistration(BaseModel):
    username: str
    email: str
    password: str
    group: int  # Добавлено новое поле
    course: int  # Добавлено новое поле
    first_name: str  # Добавлено новое поле
    last_name: str  # Добавлено новое поле


SECRET_KEY = "BEBRA228"
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

    if session.query(User).filter(User.username == user_in.username).first() is not None:
        raise HTTPException(status_code=400, detail="Username already registered")

    if session.query(User).filter(User.email == user_in.email).first() is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=user_in.username,
        email=user_in.email,
        password=user_in.password,
        group=user_in.group,
        course=user_in.course,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
    )

    session.add(user)
    session.commit()

    return {"username": user.username, "email": user.email, "group": user.group, "course": user.course, "first_name": user.first_name, "last_name": user.last_name}


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


@app.get("/profile")
async def read_users_profile(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "group": current_user.group,
        "course": current_user.course,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
    }

from typing import List
@app.get("/students", response_model=List[dict])
async def get_students_by_group(current_user: User = Depends(get_current_user)):
    session = SessionLocal()

    # Получаем список студентов с той же группы, что и текущий пользователь
    students = (
        session.query(User)
        .filter(User.group == current_user.group, User.id != current_user.id)  # Добавлен фильтр для исключения текущего пользователя
        .all()
    )

    # Преобразуем результат в список словарей для возврата в JSON
    students_data = [
        {
            "username": student.username,
            "email": student.email,
            "group": student.group,
            "course": student.course,
            "first_name": student.first_name,
            "last_name": student.last_name,
        }
        for student in students
    ]

    return students_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="main:app", reload=True)
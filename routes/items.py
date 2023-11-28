from fastapi import FastAPI, Depends, HTTPException
from validators.models import *
from sqlalchemy.orm import sessionmaker, Session, relationship
from db.database import *
from config.dependencies import *

item = FastAPI()

# Эндпоинт для регистрации нового пользователя
@item.post("/register")
async def register(user_in: UserInRegistration, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_in.username).first() is not None:
        raise HTTPException(status_code=400, detail="Username already registered")

    if db.query(User).filter(User.email == user_in.email).first() is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=user_in.username,
        email=user_in.email,
        password=user_in.password,
    )

    db.add(user)
    db.commit()

    return {
        "username": user.username,
        "email": user.email,
    }


# Эндпоинт для обновления информации о пользователе
@item.post("/user-info")
async def user_info(
    user_details: UserRegistrationDetails, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    existing_user = db.merge(current_user)

    existing_user.group = user_details.group
    existing_user.course = user_details.course
    existing_user.number = user_details.number
    existing_user.isGrant = user_details.isGrant
    existing_user.isScholarship = user_details.isScholarship

    db.commit()

    return {
        "group": existing_user.group,
        "course": existing_user.course,
        "number": existing_user.number,
        "isGrant": existing_user.isGrant,
        "isScholarship": existing_user.isScholarship,
    }


# Эндпоинт для получения токена доступа
@item.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter((User.username == form_data.username) | (User.email == form_data.username))
        .first()
    )

    if not user or user.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@item.get("/profile")
async def read_users_profile_with_grades(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Fetch user's grades and comments
    user_grades = db.query(Grade).filter(Grade.student_id == current_user.id).all()

    # Extract relevant information for each grade
    grades_data = [
        {
            "value": grade.value,
            "comment": grade.comment,
            "teacher": {
                "username": grade.teacher.username,
                "email": grade.teacher.email,
                "role": grade.teacher.role,
            },
        }
        for grade in user_grades
    ]

    # Create a response payload
    profile_data = {
        "username": current_user.username,
        "email": current_user.email,
        "group": current_user.group,
        "course": current_user.course,
        "number": current_user.number,
        "isGrant": current_user.isGrant,
        "isScholarship": current_user.isScholarship,
        "grades": grades_data,
    }

    return profile_data

# Эндпоинт для получения списка одногруппников
from typing import List

@item.get("/classmates", response_model=List[dict])
async def get_students_by_group(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    students = (
        db.query(User)
        .filter(User.group == current_user.group, User.id != current_user.id)
        .all()
    )

    students_data = [
        {
            "username": student.username,
            "email": student.email,
            "group": student.group,
            "course": student.course,
            "number": student.number,
            "isGrant": student.isGrant,
            "isScholarship": student.isScholarship,
        }
        for student in students
    ]

    return students_data



# Эндпоинт для получения списка студентов (только для учителей)
@item.get("/students", response_model=List[dict])
async def get_all_students(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Доступ запрещен. Недостаточно прав")

    students = db.query(User).filter(User.role == "student").all()

    students_data = [
        {
            "username": student.username,
            "email": student.email,
            "group": student.group,
            "course": student.course,
            "number": student.number,
            "isGrant": student.isGrant,
            "isScholarship": student.isScholarship,
        }
        for student in students
    ]

    return students_data


# Эндпоинт для отправки оценки с комментарием
@item.post("/students/{student_id}/add-grade")
async def add_grade_to_student(
    student_id: int, grade_in: GradeIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    # Check if the current user has the role of a teacher
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Доступ запрещен. Недостаточно прав")

    # Check if the student to receive the grade exists
    student_to_grade = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student_to_grade:
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Create a new grade entry
    new_grade = Grade(value=grade_in.value, comment=grade_in.comment, teacher_id=current_user.id, student_id=student_id)

    # Add the grade to the database
    db.add(new_grade)
    db.commit()

    return {"message": f"Оценка добавлена для студента с ID {student_id}"}


@item.put("/users/{user_id}/change-role")
async def change_user_role(
    user_id: int, role_change: ChangeUserRole, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    # Check if the current user has the role of a teacher
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Доступ запрещен. Недостаточно прав")

    # Check if the user to be modified exists
    user_to_change = db.query(User).filter(User.id == user_id).first()
    if not user_to_change:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Modify the user's role
    user_to_change.role = role_change.new_role
    db.commit()

    return {"message": f"Роль пользователя с ID {user_id} изменена на {role_change.new_role}"}
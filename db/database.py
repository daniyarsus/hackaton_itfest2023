from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

DATABASE_URL = "sqlite:///./test.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="teacher")
    group = Column(String, default="")
    course = Column(Integer, default="")
    number = Column(String, default="")
    isGrant = Column(Boolean, default=False)
    isScholarship = Column(Boolean, default=False)

    grades = relationship("Grade", back_populates="student", foreign_keys="[Grade.student_id]")


class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    teacher_id = Column(Integer, ForeignKey("users.id"))
    value = Column(String)
    comment = Column(String, default="")

    student = relationship("User", back_populates="grades", foreign_keys="[Grade.student_id]")
    teacher = relationship("User", foreign_keys="[Grade.teacher_id]")


Base.metadata.create_all(bind=engine)
from pydantic import BaseModel


class UserIn(BaseModel):
    username: str
    password: str


class UserInRegistration(BaseModel):
    username: str
    email: str
    password: str


class UserRegistrationDetails(BaseModel):
    group: int
    course: int
    number: str
    isGrant: bool
    isScholarship: bool


class GradeIn(BaseModel):
    value: str
    comment: str = ""

class ChangeUserRole(BaseModel):
    new_role: str
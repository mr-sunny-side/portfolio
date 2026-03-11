from sqlmodel import SQLModel
from pydantic import BaseModel

class Token(BaseModel):
	access_token: str
	token_type: str

class User(BaseModel):
	username: str
	full_name: str | None = None
	email: str | None = None
	disabled: bool | None = None

class UserInDB(User):
	hashed_password: str

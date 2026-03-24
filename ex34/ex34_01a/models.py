from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel

class Token(BaseModel):
	access_token: str
	token_type: str

class Item(BaseModel):
	name: str
	price: int = Field(ge=0)

class User(BaseModel):
	username: str
	password: str
	email: str | None = None
	disabled: bool | None = False

class UserResponse(BaseModel):
	id: int
	username: str
	email: str
	disabled: bool
	items: list["ItemEx01a"] = Relationship(back_populates="owner")

class ItemResponse(BaseModel):
	id: int
	name: str
	price: int

class UserEx01a(SQLModel, table=True):
	id: int = Field(default=None, primary_key=True)
	username: str
	password: str
	email: str | None
	disabled: bool
	items: list["ItemEx01a"] = Relationship(back_populates="owner")

class ItemEx01a(SQLModel, table=True):
	id: int = Field(default=None, primary_key=True)
	name: str
	price: int
	user_id: int = Field(default=None, foreign_key="userex01a.id")
	owner: "UserEx01a" = Relationship(back_populates="items")

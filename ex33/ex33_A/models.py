from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship

class Token(BaseModel):
	access_token: str
	token_type: str

class User(BaseModel):
	username: str
	password: str
	email: str | None = None

class Item(BaseModel):
	name: str
	price: int = Field(ge=0)

class UserResponse(BaseModel):
	id: int = Field(default=None, primary_key=True)
	username: str
	email: str | None = None
	items: list["ItemEx01"] = Relationship(back_populates="owner")

class ItemResponse(BaseModel):
	id: int
	name: str
	price: int

class UserEx01(SQLModel):
	id: int = Field(default=None, primary_key=True)
	username: str
	password: str
	email: str | None = None
	items: list["ItemEx01"] = Relationship(back_populates="owner")

class ItemEx01(SQLModel):
	id: int = Field(default=None, primary_key=True)
	user_id: int = Field(default=None, foreign_key="userex01.id")
	name: str
	price: int
	owner: "UserEx01" = Relationship(back_populates="items")

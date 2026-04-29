from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship

class Token(BaseModel):
	access_token: str
	token_type: str

class Item(BaseModel):
	name: str
	price: int = Field(ge=0)

class ItemResponse(BaseModel):
	id: int
	name: str
	price: int

class ItemDB(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	user_id : int | None = Field(default=None, foreign_key="userdb.id")
	name: str
	price: int
	owner: "UserDB" = Relationship(back_populates="items")

class User(BaseModel):
	username: str
	password: str
	email: str | None = None
	disabled: bool = False

class UserResponse(BaseModel):
	id: int
	username: str
	email: str | None
	disabled: bool
	items: list[ItemResponse] = []

class UserDB(SQLModel, table=True):
	id: int = Field(default=None, primary_key=True)
	username: str
	password: str
	email: str | None
	disabled: bool
	items: list["ItemDB"] = Relationship(back_populates="owner")

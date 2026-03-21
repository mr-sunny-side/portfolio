from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship

class Token(BaseModel):
	access_token: str
	token_type: str

class User(BaseModel):
	username: str
	password: str
	email: str | None = None

class UserResponse(BaseModel):
	id: int
	username: str
	email: str | None = None

class Item(BaseModel):
	name: str
	price: int

class ItemResponse(BaseModel):
	id: int
	name: str
	price: int

class UserEx01(SQLModel, table=True):
	id: int = Field(default=None, primary_key=True)
	username: str
	password: str
	email: str | None = None
	disabled: bool = False
	items: list["ItemEx01"] = Relationship(back_populates="owner")	# Itemテーブルとの関連付け、参照ができる

class ItemEx01(SQLModel, table=True):
	id: int = Field(default=None, primary_key=True)
	name: str
	price: int
	user_id: int | None = Field(default=None, foreign_key="userex01.id")	# Userテーブルのidを関連付けて付与、小文字でかく
	owner: "UserEx01" = Relationship(back_populates="items")

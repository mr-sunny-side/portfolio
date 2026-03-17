from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship


# 受取用Item型
class Item(BaseModel):
	name: str
	price: int = Field(ge=0)

# レスポンス用Item型
class ItemResponse(SQLModel):
	id: int
	name: str
	price: int = Field(ge=0)

# ユーザーから受取用Userデータ型
class User(BaseModel):
	username: str
	password: str
	email: str | None = None

# レスポンス用Userデータ型
class UserResponse(User):
	id: int
	username: str
	email: str | None = None
	disabled: bool | None = False
	items: list[ItemResponse] | None = None

class Token(BaseModel):
	access_token: str
	token_type: str

class UserEx07(SQLModel):
	id: int | None = Field(default=None, primary_key=True)
	username: str
	password: str
	email: str | None = None
	disabled: bool | None = False
	items = list[ItemResponse] | None = None

class ItemEx07(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	name: str
	price: int
	user_id: int | None = Field(default=None, foreign_key=UserEx07.id)	# UserDBとの紐付け
	owner: "UserEx07" | None = Relationship(back_populates="Items")		# User型でのItem型の定義

from pydantic import BaseModel
from sqlmodel import SQLModel, Field

# クライアントからの受取用型
class Item(BaseModel):
	name: str
	price: int = Field(ge=0)

# レスポンス用Item型
class ItemResponse(Item):
	id: int

class ItemEx06(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	name: str
	price: int

# クライアントからの受取用User型
class User(BaseModel):
	username: str
	email: str | None = None
	hashed_password: str	# DBと同じにしないと、モデル変換ができない

# クライアントレスポンス用User型
class UserResponse(BaseModel):
	id: int
	username: str
	email: str | None = None
	disabled: bool | None = False

class UserEx06(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	username: str
	hashed_password: str
	email: str | None = None
	disabled: bool | None = False

class Token(BaseModel):
	access_token: str
	token_type: str

class TokenData(BaseModel):
	username: str

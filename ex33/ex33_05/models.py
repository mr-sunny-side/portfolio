from sqlmodel import SQLModel, Field
from pydantic import BaseModel

# トークンリクエスト用のトークン格納型
class Token(BaseModel):
	access_token: str
	token_type: str

# トークンのでー田を取り出すようの型
class TokenData(BaseModel):
	username: str

# ユーザーレスポンス用の型
class User(BaseModel):
	username: str
	full_name: str | None = None
	email: str | None = None
	disabled: bool | None = None

# ハッシュも含めたユーザーデータ型
class UserInDB(User):
	hashed_password: str

# クライアントからの受取用Item型
class Item(BaseModel):
	name: str
	price: int = Field(ge=0)

# DB用Item型
class ItemEx05(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	name: str
	price: int

class ItemResponse(BaseModel):
	id: int
	name: str
	price: int

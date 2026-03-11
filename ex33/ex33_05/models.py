from sqlmodel import SQLModel
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

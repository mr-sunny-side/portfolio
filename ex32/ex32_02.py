from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from pydantic import BaseModel

app = FastAPI()

# クライアントのヘッダーからbearerヘッダーを取り出すオブジェクト
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

# ユーザーが送る情報
class User(BaseModel):
	username: str
	email: str | None = None
	full_name: str | None = None
	disabled: bool | None = None

# JWTトークンのpayloadをデコードしてユーザー情報を取り出す関数
def fake_decode_token(token):
	return User(username=token + "decoded")

# fake_decode_tokenにトークンを渡し、userインスタンスを返す関数
async def get_current_user(token: Annotated[str, Depends(oauth2)]):
	user = fake_decode_token(token)
	return user

@app.get("/users/me")
async def read_users_me(cur_user: Annotated[User, Depends(get_current_user)]):
	return cur_user

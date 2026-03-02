
"""
	03-02: トークン受け取り後の記述から

"""

from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "hashed_password": "fakehashedsecret",  # "fakehashed" + "secret"
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "hashed_password": "fakehashedsecret2",  # "fakehashed" + "secret2"
        "disabled": True,  # ← 無効ユーザー
    },
}

oauth2 = OAuth2PasswordBearer(tokenUrl="token")

# 開示用クラス(パスワードなし)
class User(BaseModel):
	username: str
	email: str | None = None
	full_name: str | None = None
	disabled: bool | None = None

# DB用クラス(パスワードあり)
class UserInDB(User):
	hashed_password: str

def fake_hashed_pass(request_pass: str):
	return "fakehashed" + request_pass

@app.get("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
	# ユーザーがdbに存在するか確認
	user_dict = fake_users_db.get(form_data.username)	# 対応するユーザー情報を取得
	if not user_dict:
		raise HTTPException(status_code=400, detail="User not found")
	user = UserInDB(**user_dict)

	# パスワードが一致するか確認
	request_pass = fake_hashed_pass(form_data.password)	# ハッシュ？をつける模擬関数
	if request_pass != user.hashed_password:
		raise HTTPException(status_code=400, detail="Password is incorrect")
	return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def handle_users(
	token: Annotated[str, Depends(oauth2)]
):
	# トークン受け取り後から

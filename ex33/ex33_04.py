"""
	03-09:	トークンの記述から
			- /users/meから

"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from pydantic import BaseModel
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import jwt

fake_users_db = {
	"johndoe": {
		"username": "johndoe",
		"full_name": "John Doe",
		"email": "johndoe@example.com",
		"hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
		"disabled": False,
	}
}

app = FastAPI()
load_dotenv()

DUMMY_HASH = "dummyhash"
KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

class User(BaseModel):
	username: str
	full_name: str | None = None
	email: str | None = None
	disabled: bool | None = None

class UserInDB(User):
	hashed_password: str

class Token(BaseModel):
	access_token: str
	token_type: str

def auth_user(
	fake_db, username: str, password: str
) -> UserInDB | None:

	# ハッシュ関係のインスタンスを取得
	hasher = PasswordHash.recommended()

	# ユーザーが存在するか確認
	if username not in fake_db:
		hasher.verify(password, DUMMY_HASH)	# 疑似検証でタイミング剛撃対策
		return None

	# ユーザー情報を取得、ハッシュを検証
	user = UserInDB(**fake_db[username])
	if not hasher.verify(password, user.hashed_password):
		return None
	return user

def create_token(
	user_sub: dict,
	token_expire: timedelta | None = None
):
	# 作業用にsubをコピー
	token_sub = user_sub.copy()

	#有効期限を設定
	if token_expire:
		expire = datetime.now(timezone.utc) + token_expire
	else:
		expire =datetime.now(timezone.utc) + timedelta(minutes=15)

	# トークンの作成
	token_sub.update({"exp": expire})
	token = jwt.encode(token_sub, key=KEY, algorithm=ALGORITHM)
	return token

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
	# ユーザー認証
	user = auth_user(
		fake_users_db,
		form_data.username,
		form_data.password
	)

	# 認証できなければエラー
	if not user:
		raise HTTPException(
			status_code=401,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"}
		)

	# トークンの作成
	token_expire = timedelta(minutes=30)
	token = create_token(
		user_sub={"sub": form_data.username},
		token_expire=token_expire
	)

	return Token(
		access_token=token,
		token_type="Bearer"
	)

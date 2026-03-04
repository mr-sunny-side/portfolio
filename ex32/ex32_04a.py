
"""
	03-04: /users/meの記述から

"""

import jwt
from typing import Annotated
from pydantic import BaseModel
from pwdlib import PasswordHash
from datetime import timedelta, datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

DUMMY_HASH = "dummyhash"
TOKEN_EXPIRE = 30
ALGORITHM = "HS256"

# openssl rand -hex 32
KEY = "0416ae60c51e518c43ce4ce1704153a259d47dee19bbf9564bf0e2c9c3ac87e3"

app = FastAPI()

fake_users_db = {
	"johndoe": {
		"username": "johndoe",
		"full_name": "John Doe",
		"email": "johndoe@example.com",
		"hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
		"disabled": False,
	}
}

# クライアントに返すトークンモデル
class Token(BaseModel):
	access_token: str
	token_type: str

# クライアントレスポンス用のユーザー情報クラス
class User(BaseModel):
	username: str
	email: str | None = None
	full_name: str | None = None
	disabled: bool | None = None

# DB用のユーザー情報クラス
class UserInDB(User):
	hashed_pass: str

def authenticate_user(
		fake_db, username: str, password: str
) -> UserInDB | None:
	"""
	# パスとユーザーが正しい確認する関数

	1. ユーザーがDBに存在するか確認
		- 存在しないなら疑似確認を走らせる
	2. UserInDBにユーザー情報を変換
	3. ハッシュを確認
	4. UserInDBインスタンスをreturn

	"""
	# ユーザーが存在しないなら疑似確認を走らせる
	if not username in fake_db:
		PasswordHash.verify(password, DUMMY_HASH)
		return None

	# DB用インスタンスに変換
	user = UserInDB(**fake_db[username])

	# パスワードがハッシュと一致するか確認
	if not PasswordHash.verify(password, user.hashed_pass):
		return None
	return user


def create_token(username: dict, expires_delta: timedelta | None = None):
	"""
	# JWTトークンを作成する関数

	1. 作業用にusername(sub dict)をコピー
	2. 有効期限を作成
	3. トークンを反映し、作成

	"""
	response = username.copy()

	# 有効期間の指定があれば対応
	if expires_delta:
		expire = datetime.now(timezone.utc) + expires_delta	# JWTは必ずUTCでdeltaを作成
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=15)

	# トークンの作成
	response.update({"exp": expire})
	encoded = jwt.encode(response, KEY, algorithm=ALGORITHM)# トークンをkeyを使ってalgorithmの形式にエンコード
	return encoded

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
	"""
	1. authenticate_userで、ユーザーの存在・ハッシュの一致を確認
		- 存在しないなら401
	2. create_access_tokenでJWTトークンを作成
		- timedeltaで有効期限を設定
	3. Tokenインスタンスをレスポンス
	"""
	# UserInDBインスタンスを取得
	user = authenticate_user(fake_users_db, form_data.username, form_data.password)

	# インスタンスが無いなら認証失敗で401
	if not user:
		raise HTTPException(
			status_code=401,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"}	# クライアントに認証方法を伝える
		)

	# トークンを作成
	token_expires = timedelta(minutes=TOKEN_EXPIRE)	# 有効期限設定用のtimedeltaを作成
	token = create_token(
		{"sub": user.username},
		token_expires
	)
	return Token(access_token=token, token_type="bearer")

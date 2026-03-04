
"""
	03-04: /users/meの記述から

"""

import jwt
from jwt.exceptions import InvalidTokenError
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
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

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

class TokenData(BaseModel):
	username: str | None = None

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

async def get_cur_user(
	token: Annotated[str, Depends(oauth2)]
):
	"""
	# JWTトークンをデコードして認証を確認する関数

	1. トークンのデコード
	2. デコードしたトークンからusernameを取得
	3. TokenDataインスタンスとしてユーザー名を取得
	4. dbに存在するか確認し、UserInDBインスタンスに変換
	5. インスタンスをreturn

	"""
	# 認証失敗時のエラーレスポンス
	error_detail = HTTPException(
		status_code=401,
		detail="Authentication failed",
		headers={"WWW-Authenticate": "Bearer"}
	)

	try:
		# JWTトークンをデコード
		payload = jwt.decode(token, KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")	# デコードしたトークンからusername取り出し
		if username is None:			# ユーザー名が入ってない可能性もある
			raise error_detail
		token_data = TokenData(username=username)	# 将来payloadの内容が増えるかも、なのでここで一旦インスタンス化
	except InvalidTokenError:
		raise error_detail

	# ユーザーが存在するかの確認
	if token_data.username not in fake_users_db:
		raise error_detail

	# UserInDBに変換
	username = token_data.username
	user = UserInDB(**fake_users_db[username])
	return user



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

@app.get("/users/me")
async def handle_users(
	cur_user: Annotated[User, Depends(get_cur_user)]	#
) -> User:	# 関数の戻り値とレスポンスが一致しているので、response_modelはいらない
	return cur_user

"""
	03-04:	4aの復習から
			create_tokenの記述から

"""
from datetime import datetime, timedelta
from pwdlib import PasswordHash
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

fake_users_db = {
	"johndoe": {
		"username": "johndoe",
		"full_name": "John Doe",
		"email": "johndoe@example.com",
		"hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
		"disabled": False,
	}
}

DUMMY_HASH = "dummyhash"
TOKEN_EXPIRE = 30

app = FastAPI()

# クライアントへレスポンス用のモデル
class User(BaseModel):
	username: str
	email: str | None = None
	full_name: str | None = None
	disabled: bool | None = None

class UserInDB(User):
	hashed_password: str

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
	# ハッシュ関係の動作をするためのインスタンスを作成
	pwd_hasher = PasswordHash.recommended()

	# ユーザーが存在するか確認
	if not username in fake_db:
		pwd_hasher.verify(password, DUMMY_HASH)
		return None

	# 検証のためユーザー情報を取り出し
	user = UserInDB(**fake_db[username])

	# ハッシュが一致するか確認
	if not pwd_hasher.verify(password, user.hashed_password):
		return None
	return user



def create_token():
	"""
	# JWTトークンを作成する関数

	1. 作業用にusername(sub dict)をコピー
	2. 有効期限を作成
	3. トークンを反映し、作成

	"""
	pass


async def get_cur_user():
	"""
	# JWTトークンをデコードして認証を確認する関数

	1. トークンのデコード
	2. デコードしたトークンからusernameを取得
	3. TokenDataインスタンスとしてユーザー名を取得
	4. dbに存在するか確認し、UserInDBインスタンスに変換
	5. インスタンスをreturn

	"""

	pass

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
	"""
	1. authenticate_userで、ユーザーの存在・ハッシュの一致を確認
		- ユーザーデータを取得
		- 存在しないなら401
	2. create_tokenでJWTトークンを作成
		- timedeltaで有効期限を設定
	3. Tokenインスタンスをレスポンス

	"""
	# フォームデータを検証、失敗なら401
	user = authenticate_user(fake_users_db, form_data.username, form_data.password)
	if not user:
		raise HTTPException(
			status_code=401,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "bearer"}
		)

	# トークンを作成
	token_expires = timedelta(minutes=TOKEN_EXPIRE)	# 有効期限を作成

"""
	03-04:	4aの復習から
			create_tokenの記述から

"""
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
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
KEY = "3a81e68db8edc24614d0d98d51bf84db1735dbc5496d1fee466a6040e43d121b"
ALGORITHM = "HS256"

app = FastAPI()
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

# クライアントへレスポンス用のモデル
class User(BaseModel):
	username: str
	email: str | None = None
	full_name: str | None = None
	disabled: bool | None = None

class UserInDB(User):
	hashed_password: str

# クライアントに返すトークンモデル
class Token(BaseModel):
	access_token: str
	token_type: str

class TokenData(BaseModel):
	username: str | None = None

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



def create_token(
	username: dict, expires_delta : timedelta | None = None
):
	"""
	# JWTトークンを作成する関数

	1. 作業用にusername(sub dict)をコピー
	2. 有効期限を作成
	3. トークンを反映し、作成

	"""
	# 作業、レスポンス用にユーザーネームをコピー
	response = username.copy()

	# 有効期限が設定されていたら、deltaを作成
	if expires_delta:
		expire = datetime.now(timezone.utc) + expires_delta
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=15)

	# トークンの作成
	response.update({"exp": expire})
	encoded = jwt.encode(response, KEY, algorithm=ALGORITHM)
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
	# 承認失敗時のエラーレスポンス
	error_detail = HTTPException(
		status_code=401,
		detail="Authentication failed",
		headers={"WWW-Authenticate": "Bearer"}
	)

	try:
		#JWTトークンをデコード
		payload = jwt.decode(token, KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise error_detail
		token_data = TokenData(username=username)
	except InvalidTokenError:
		raise error_detail

	if token_data.username not in fake_users_db:
		raise error_detail

	user = UserInDB(**fake_users_db[token_data.username])
	return user

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
	encoded_token = create_token(
		username={"sub": user.username},
		expires_delta=token_expires
	)

	return Token(
		access_token=encoded_token,
		token_type="bearer"
	)

@app.get("/users/me")
async def handle_users(
	cur_user: Annotated[User, Depends(get_cur_user)]
) -> User:
	return cur_user

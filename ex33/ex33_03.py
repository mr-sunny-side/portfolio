"""
	03-08:	認証の実装
			- テストから
			itemエンドポイントの実装(items/idも)とデータベースの連携

"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated
from pydantic import BaseModel
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import jwt
from jwt.exceptions import InvalidTokenError


load_dotenv()
app = FastAPI()
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

DUMMY_HASH = "dummyhash"
TOKEN_EXPIRE = 30
KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


fake_users_db = {
	"johndoe": {
		"username": "johndoe",
		"full_name": "John Doe",
		"email": "johndoe@example.com",
		"hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
		"disabled": False,
	}
}

# クライアントに渡すトークンの型
class Token(BaseModel):
	access_token: str
	token_type: str

# デコードしたトークンから情報を取り出す用の型
class TokenData(BaseModel):
	username: str

# クライアントに渡すユーザー情報型
class User(BaseModel):
	username: str
	full_name: str | None = None
	email: str | None = None
	disabled: bool | None = None

# DBで管理するハッシュありユーザー情報型
class UserInDB(User):
	hashed_password: str

def auth_user(
	fake_db, username: str, password: str
) -> UserInDB | None:
	hasher = PasswordHash.recommended()

	# ユーザーの存在を確認
	if username not in fake_db:
		hasher.verify(password, DUMMY_HASH)
		return None

	# ユーザー情報を取得
	user = UserInDB(**fake_db[username])

	# パスの検証
	if not hasher.verify(password, user.hashed_password):
		return None
	return user

def create_token(
	user_sub: dict,
	token_expire: timedelta | None = None
) -> str:
	# 戻り値のためのsubをコピー作成
	response = user_sub.copy()

	# 有効期限を設定
	if token_expire:
		expire = datetime.now(timezone.utc) + token_expire
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=15)

	# トークンを作成
	response.update({"exp": expire})
	encoded = jwt.encode(response, KEY, algorithm=ALGORITHM)
	return encoded

def	get_cur_user(
	token: Annotated[str, Depends(oauth2)]
) -> UserInDB:
	"""
	# JWTトークンをデコードして認証を確認する関数

	1. トークンのデコード
	2. デコードしたトークンからusernameを取得
	3. TokenDataインスタンスとしてユーザー名を取得
	4. dbに存在するか確認し、UserInDBインスタンスに変換
	5. インスタンスをreturn

	"""
	error_detail = HTTPException(
		status_code=401,
		detail="Authentication failed",
		headers={"WWW-Authenticate": "Bearer"}
	)

	try:
		payload = jwt.decode(token, KEY, algorithms=[ALGORITHM])
		username = payload['sub']
		if not username:
			raise error_detail
		token_data = TokenData(username=username)
	except InvalidTokenError:
		raise error_detail

	user = UserInDB(**fake_users_db[token_data.username])
	return user


@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
	"""
	1. authenticate_userで、ユーザーの存在・ハッシュの一致を確認
		- ユーザーデータを取得
		- 存在しないなら401
	2. create_tokenでJWTトークンを作成
		- timedeltaで有効期限を設定
	3. Tokenインスタンスをレスポンス

	"""
	# ユーザーの存在、パスの一致を検証
	user = auth_user(fake_users_db, form_data.username, form_data.password)
	if not user:
		raise HTTPException(
			status_code=401,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"}
		)

	# expire期間を定義し、トークンを作成
	token_expire = timedelta(minutes=TOKEN_EXPIRE)
	token = create_token(
		user_sub={"sub": user.username},
		token_expire=token_expire
	)

	return Token(
		access_token=token,

		token_type="Bearer"
	)

@app.get("/users/me")
async def handle_me(
	cur_user: Annotated[User, Depends(get_cur_user)]
) -> User:
	return cur_user

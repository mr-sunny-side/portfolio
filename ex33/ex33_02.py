
"""
	03-07:	ex32の復習から
			テストから

"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from dotenv import load_dotenv
import os
import jwt
from jwt.exceptions import InvalidTokenError
from typing import Annotated
from pydantic import BaseModel
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone

app = FastAPI()
load_dotenv()	# .envから環境変数を展開
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

DUMMY_HASH = "dummyhash"
TOKEN_EXPIRE = 30
KEY = os.getenv("SECRET_KEY")	# 展開した環境変数を取得
ALGORITHM = os.getenv("ALGORITHM")

if not KEY or not ALGORITHM:
	raise ValueError("Cannot set KEY or ALGORITHM")

fake_users_db = {
	"johndoe": {
		"username": "johndoe",
		"full_name": "John Doe",
		"email": "johndoe@example.com",
		"hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
		"disabled": False,
	}
}

# 作成したトークンを格納するクラス
class Token(BaseModel):
	access_token: str
	token_type: str

# トークンから取得したユーザー情報を格納するクラス
class TokenData(BaseModel):
	username: str | None = None

# ユーザー応答用のユーザ情報格納クラス
class User(BaseModel):
	username: str
	email: str | None = None
	full_name: str | None = None
	disabled: bool | None = None

# ハッシュも含めたユーザー情報格納クラス
class UserInDB(User):
	hashed_password: str

def auth_user(
	fake_db, username: str, password: str
) -> UserInDB | None:
	pwd_hasher = PasswordHash.recommended()

	# ユーザーが存在するか確認
	if username not in fake_db:
		pwd_hasher.verify(password, DUMMY_HASH)	# 疑似検証を行う
		return None

	# ユーザー情報を取得
	user = UserInDB(**fake_db[username])

	# パスワードを確認
	if not pwd_hasher.verify(password, user.hashed_password):
		return None
	return user

def create_token(
		user_sub: dict,
		expire_delta: timedelta | None = None
) -> str:
	response = user_sub.copy()

	# 有効期限を設定
	if expire_delta:
		expire = datetime.now(timezone.utc) + expire_delta
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=15)

	response.update({"exp": expire})
	encoded = jwt.encode(response, KEY, algorithm=ALGORITHM)	# ３つ目以降はキーワード引数で書く慣習がある
	return encoded

def get_cur_user(
	token: Annotated[str, Depends(oauth2)]
) -> UserInDB:
	error_detail = HTTPException(
		status_code=401,
		detail="Authentication failed",
		headers={"WWW-Authenticate": "Bearer"}
	)

	try:
		# トークンをデコードし、ユーザー情報を取得
		payload = jwt.decode(token, key=KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise error_detail
		token_data = TokenData(username=username)	# ユーザー情報をトークンから取得
	except InvalidTokenError:
		raise error_detail

	# 取得したユーザー情報が存在するか確認
	if token_data.username not in fake_users_db:
		raise error_detail

	# 取得した情報をインスタンスとして展開
	user = UserInDB(**fake_users_db[token_data.username])
	return user

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:

	# ユーザー情報を取得、できなかえれば401
	user = auth_user(fake_users_db, form_data.username, form_data.password)
	if not user:
		raise HTTPException(
			status_code=401,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"}
		)

	# トークンを作成
	token_expires = timedelta(minutes=TOKEN_EXPIRE)
	encoded_token = create_token(
		user_sub={"sub": user.username},
		expire_delta=token_expires
	)

	return Token(
		access_token=encoded_token,
		token_type="Bearer"
	)

@app.get("/users/me")
async def handle_users(
	cur_user: Annotated[User, Depends(get_cur_user)]
) -> User:
	return cur_user

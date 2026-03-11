"""
	03-10:	トークン記述 - 完了
			DB記述
			マイグレーション作成(事前解説8.)

"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv
import os

from models import User, UserInDB, Token, TokenData

fake_users_db = {
	"johndoe": {
		"username": "johndoe",
		"full_name": "John Doe",
		"email": "johndoe@example.com",
		"hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
		"disabled": False,
	}
}

load_dotenv()
app = FastAPI()
oauth2 = OAuth2PasswordBearer

KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
TOKEN_EXPIRE = 30

def	auth_user(
	fake_db, username: str, password: str
) -> UserInDB | None:

	# hash関係のオブジェクトを取得
	hasher = PasswordHash.recommended()

	# ユーザーが存在するか確認
	if username not in fake_db:
		hasher.verify(password, fake_db.get("hashed_password"))
		return None

	# ユーザーデータを取得
	user = UserInDB(**fake_db[username])

	# ハッシュを確認
	if not hasher.verify(password, user.hashed_password):
		return None
	return user

def create_token(
	user_sub: dict,
	token_expire: timedelta | None = None
) -> str:
	# トークン作成用にuser_subをコピー
	token_dict = user_sub.copy()

	# 有効期限の設定
	if token_expire:
		expire = datetime.now(timezone.utc) + token_expire
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=15)

	# トークン文字列を作成
	token_dict.update({"exp": expire})
	token = jwt.encode(token_dict, key=KEY, algorithm=ALGORITHM)
	return token

def get_cur_user(
	token: Annotated[str, Depends(oauth2)]
) -> UserInDB:
	error_detail = HTTPException(
		status_code=401,
		detail="Authentication failed",
		headers={"Authenticate": "Bearer"}
	)

	try:
		payload = jwt.decode(token, key=KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise error_detail
		token_data = TokenData(username=username)
	except InvalidTokenError:
		raise error_detail

	if token_data.username not in fake_users_db:
		raise error_detail
	user = UserInDB(**fake_users_db[username])
	return user

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:

	# ユーザーの認証
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

	# トークン作成
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

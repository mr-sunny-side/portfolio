"""
	03-17: alembicの設定変更、更新から

"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import create_engine, Session, select
from typing import Annotated
from pwdlib import PasswordHash
from datetime import timedelta, datetime, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv
import os

from models import User, UserResponse, UserEx07, Token, Item, ItemResponse, ItemEx07

dummy_hasher = PasswordHash.recommended()
engine = create_engine("postgresql://ex33:secret@localhost/ex33_db")
app = FastAPI()
oauth2 = OAuth2PasswordBearer(tokenUrl="token")
load_dotenv()

DUMMY = dummy_hasher.hash("dummy")
KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
TOKEN_EXPIRE = 30

def get_session():
	with Session(engine) as session:
		yield session

# ユーザー認証関数
def auth_user(
	username: str,
	password: str,
	session: Session
) -> UserEx07 | None:
	hasher = PasswordHash.recommended()

	# userの取り出し、失敗ならnone
	statement = select(UserEx07).where(UserEx07.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		hasher.verify(password, DUMMY)	# 疑似検証で攻撃阻止
		return None

	# ハッシュの検証
	if not hasher.verify(password, db_user.password):
		return None
	return db_user

# トークン作成関数
def create_token(
	user_sub: dict,
	token_expire: timedelta | None = None
) -> str:
	# 作業用に辞書をコピー
	copy_sub = user_sub.copy()

	# 有効期限の設定
	if token_expire:
		expire = datetime.now(timezone.utc) + token_expire
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=15)

	# トークンの作成
	copy_sub.update({"exp": expire})
	token = jwt.encode(copy_sub, KEY, ALGORITHM)
	return token

def get_cur_user(
	token: Annotated[str, Depends(oauth2)],
	session: Annotated[Session, Depends(get_session)]	# エンドポイントでdependsで呼び出すので、fastapiが解決する
) -> UserEx07:
	error_detail = HTTPException(
		status_code=401,
		detail="Authentication failed",
		headers={"WWW-Authenticate": "Bearer"}
	)

	# トークンのデコード
	try:
		payload = jwt.decode(token, KEY, [ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise error_detail
	except InvalidTokenError:
		raise error_detail

	# ユーザーデータの取り出し
	statement = select(UserEx07).where(UserEx07.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		raise error_detail
	return db_user



# ユーザーをDBに登録するエンドポイント
@app.post("/users/register")
async def handle_register(
	user: User,
	session: Annotated[Session, Depends(get_session)]
) -> UserResponse:
	hasher = PasswordHash.recommended()

	# DBの形に変換し、パスワードをハッシュ化
	db_user = UserEx07.model_validate(user)
	db_user.password = hasher.hash(db_user.password)

	session.add(db_user)
	session.commit()
	session.refresh(db_user)
	return db_user

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	session: Annotated[Session, Depends(get_session)]
) -> Token:
	# ユーザー認証
	user = auth_user(
		form_data.username,
		form_data.password,
		session
	)

	# 認証失敗ならエラー
	if not user:
		raise HTTPException(
			status_code=401,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"}
		)

	# ユーザーが無効なら400
	if user.disabled == True:
		raise HTTPException(
			status_code=400,
			detail="Inactive user"
		)

	# トークンの作成
	token_expire = timedelta(minutes=TOKEN_EXPIRE)
	token = create_token(
		user_sub={"sub": user.username},
		token_expire=token_expire
	)

	return Token(
		access_token=token,
		token_type="Bearer"
	)

@app.post("/items")
async def handle_add_items(
	item: Item,
	cur_user: Annotated[UserResponse, Depends(get_cur_user)],
	session: Annotated[Session, Depends(get_session)]
) -> UserResponse:
	db_item = ItemEx07.model_validate(item)
	db_item.user_id = cur_user.id
	session.add(db_item)
	session.commit()
	session.refresh(db_item)
	return cur_user

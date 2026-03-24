"""
	03-22:	アプリの構築
			- token
			- user/register, users/me=delete, users/me/items
			- items=post, items=delete, items
			- engineの記述
			マイグレーションの作成
			dockerイメージの作成

			ex34_01の復習から(全部書き直す)
			- ex34a/ex34_01aとして復習用ディレクトリに作成
			- 新DBの作成
			- dockerの再作成
			アプリの作成


"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlmodel import Session, create_engine, select
from pwdlib import PasswordHash
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
import jwt

from models import Token, User, Item, UserResponse, ItemResponse, UserEx01a, ItemEx01a

load_dotenv()
dummy_hash = PasswordHash.recommended()
app = FastAPI()
engine = create_engine()	# ex34_02で設定

DUMMY = dummy_hash.hash("dummy")
KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def get_session():
	with Session(engine) as session:
		yield session

def auth_users(
	username: str,
	password: str,
	session: Session
) -> UserEx01a | None:
	hasher = PasswordHash.recommended()

	# ユーザー名からデータを抽出
	statement = select(UserEx01a).where(UserEx01a.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		hasher.verify(password, DUMMY)	# 疑似検証で攻撃阻止
		return None

	if not hasher.verify(password, db_user.password):
		return None
	return db_user

def create_token(
	user_sub: dict,
	token_expire: timedelta | None = None
) -> str:
	copy_sub = user_sub.copy()

	if token_expire:
		expire = datetime.now(timezone.utc) + token_expire
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=30)

	copy_sub.update({"exp": expire})
	token = jwt.encode(copy_sub, KEY, ALGORITHM)
	return token

@app.post("/token")
async def handle_all_users(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	session: Annotated[Session, Depends(get_session)]
) -> list[UserResponse]:

	# ユーザーの検証
	db_user = auth_users(
		form_data.username,
		form_data.password,
		session
	)
	if not db_user:
		raise HTTPException(
			status_code=401,
			detail="Authentication failed",
			headers={"WWW-Authenticate": "Bearer"}
		)

	# トークンの作成
	token_expire = timedelta(minutes=30)
	token = create_token(
		user_sub={"sub": db_user.username},
		token_expire=token_expire
	)

	return Token(
		access_token=token,
		token_type="Bearer"
	)

@app.post("/users/register")
async def handle_add_users(
	user: User,
	session: Annotated[Session, Depends(Session)]
) -> UserResponse:
	hasher = PasswordHash.recommended()

	# db型に整形し、パスワードをハッシュ化
	db_user = UserEx01a.model_validate(User)
	db_user.password = hasher.hash(db_user.password)

	session.add(db_user)
	session.commit()
	session.refresh(db_user)
	return db_user


@app.get("/users/me/items")
async def handle_all_users():
	# 現在のユーザーの取得(get_cur_users)

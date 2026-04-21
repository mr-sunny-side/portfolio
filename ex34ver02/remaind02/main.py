"""
	### プロジェクトdirの環境構築から
	 - 依存関係ファイルの作成(pip freeze > requirements.txt)	- 完了
	 - 新規DBの作成(kimera:secret/ex34)							- 完了
	 - alembicのインストール									- 完了
	 - .envファイルの作成										- 完了

	### アプリの構築
	 - token											 - 完了
	 - user/register									 - 完了
	 - users=get										 -
	 - users=delete										 -
	 - items=post										 -
	 - items=delete										 -
	 - コードのレビュー									 -

	 - dockerイメージの作成								 -
	 - engineの記述(db:5433へ接続)						 -
	 - マイグレーションの作成(コンテナ内で実行)			 -


"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, create_engine, select
from typing import Annotated
from dotenv import load_dotenv
import os
from pwdlib import PasswordHash
from datetime import datetime, timezone, timedelta
import jwt

from models import User, Item, UserResponse, ItemResponse, UserDB, ItemDB, Token

HASHER = PasswordHash.recommended()
DUMMY = HASHER.hash("dummy")
DATABASE_URL = os.environ("DATABASE_URL")	# ymlファイルで設定した環境変数からURLを取得
KEY = os.environ("SECRET_KEY")
ALGORITHM = os.environ("ALGORITHM")

app = FastAPI()
engine = create_engine(DATABASE_URL)

def get_session():
	with Session(engine) as session:
		yield session

def auth_user(
	username: str,
	password: str,
	session: Session
) -> UserDB | None:

	# ユーザー情報の取得
	statement = select(UserDB).where(UserDB.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		HASHER.verify(password, DUMMY)	# 取得失敗なら疑似検証
		return None

	# パスワードの検証
	if not HASHER.verify(password, db_user.password):
		return None
	return db_user

def create_token(
	user_sub: dict,
	token_expire: timedelta | None = None
) -> str:
	copy_sub = user_sub.copy()

	# 有効期限の設定
	if token_expire:
		expire = datetime.now(timezone.utc) + token_expire
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=30)

	# トークンの作成
	copy_sub.update({"exp": expire})
	token = jwt.encode(copy_sub, KEY, ALGORITHM)
	return token

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	session: Annotated[Session, Depends(get_session)]
) -> Token:

	# ユーザーの承認、取得
	db_user = auth_user(
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
	session: Annotated[Session, Depends(get_session)]
) -> UserResponse:

	# ユーザーDB型に変換, パスワードをハッシュ化
	db_user = UserDB.model_validate(user)
	db_user.password = HASHER.hash(db_user.password)

	# DBに保存
	session.add(db_user)
	session.commit()
	session.refresh(db_user)
	return db_user

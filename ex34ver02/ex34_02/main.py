"""
	04-08: プロジェクトdirの環境構築から
	 - 依存関係ファイルの作成(pip freeze > requirements.txt)	- 完了
	 - 新規DBの作成(kimera:secret/ex34)							- 完了
	 - alembicのインストール									- 完了
	 - .envファイルの作成										- 完了

	03-22:	アプリの構築
	 - token											 -
	 - user/register, users/me=delete, users/me/items	 -
	 - items=post, items=delete							 -
	 - dockerイメージの作成								 -
	 - engineの記述(db:5433へ接続)						 -
	 - マイグレーションの作成(コンテナ内で実行)			 -



"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import create_engine, Session, select
from typing import Annotated
from pwdlib import PasswordHash
from datetime import datetime, timezone, timedelta
import jwt
import os
from dotenv import load_dotenv

from models import User, UserResponse, UserDB, Item, ItemResponse, ItemDB, Token

load_dotenv()
app = FastAPI()
engine = create_engine() # 後で入力
dummy_hasher = PasswordHash.recommended()

KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
DUMMY = dummy_hasher.hash("dummy")

def get_session():
	with Session(engine) as session:
		yield session

def auth_users(
	username: str,
	password: str,
	session: Session
) -> UserDB | None:
	hasher = PasswordHash.recommended()

	# ユーザー名からデータを取得、失敗ならnone
	statement = select(UserDB).where(UserDB.username == username)
	db_user = session.exec(statement).first()	# 最初の一件だけ取得
	if not db_user:
		hasher.verify(password, DUMMY)	# 疑似検証
		return None

	# パスワードを検証
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

# ユーザーのトークン発行
@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	session: Annotated[Session, Depends(get_session)]
) -> Token:
	# ユーザーの検証, 失敗なら401
	db_user = auth_users(
		form_data.username,
		form_data.password,
		session
	)
	if not db_user:
		raise HTTPException(
			status_code=401,
			detail="Authenticate failed",
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
		token_type="bearer"
	)

# ユーザーの追加
@app.post("/users/register")
async def handle_add_users(
	user: User,
	session: Annotated[Session, Depends(get_session)]
) -> UserResponse:
	hasher = PasswordHash.recommended()

	# db型に変換、パスワードをハッシュ化
	db_user = UserDB.model_validate(user)
	db_user.password = hasher.hash(db_user.password)

	# dbに保存
	session.add(db_user)
	session.commit()
	session.refresh(db_user)
	return db_user

"""
	03-22:	アプリの構築
			- token											 - 完了
			- user/register, users/me=delete, users/me/items - 完了
			- items=post, items=delete						 - 完了
			- dockerイメージの作成							 - 完了
			- engineの記述									 - 完了
			- マイグレーションの作成						 - 完了

			ex34_01の復習から(全部書き直す)
			- ex34a/ex34_01aとして復習用ディレクトリに作成
			- 新DBの作成
			- dockerの再作成
			アプリの作成


"""
from fastapi import FastAPI, Depends, HTTPException, Response, Path
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated
from sqlmodel import Session, create_engine, select
from pwdlib import PasswordHash
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError

from models import Token, User, Item, UserResponse, ItemResponse, UserEx01a, ItemEx01a
# コンテナ内のappからの相対パスで記述

load_dotenv()
dummy_hash = PasswordHash.recommended()
app = FastAPI()
engine = create_engine("postgresql://ex33:secret@localhost/ex33_db")	# ex34_02で設定
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

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

def get_cur_users(
	token: Annotated[str, Depends(oauth2)],
	session: Annotated[Session, Depends(get_session)]
) -> UserEx01a:
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

	# トークンの情報でデータ取り出し
	statement = select(UserEx01a).where(UserEx01a.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		raise error_detail
	return db_user

# トークンの取得
@app.post("/token")
async def handle_all_users(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	session: Annotated[Session, Depends(get_session)]
) -> Token:

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

# ユーザーの追加
@app.post("/users/register")
async def handle_add_users(
	user: User,
	session: Annotated[Session, Depends(get_session)]
) -> UserResponse:
	hasher = PasswordHash.recommended()

	# db型に整形し、パスワードをハッシュ化
	db_user = UserEx01a.model_validate(user)
	db_user.password = hasher.hash(db_user.password)

	session.add(db_user)
	session.commit()
	session.refresh(db_user)
	return db_user


# 自分のアイテム情報も含めた参照
@app.get("/users/me/items")
async def handle_all_users(
	cur_user: Annotated[UserResponse, Depends(get_cur_users)]
) -> UserResponse:
	return cur_user

# ユーザーの削除
@app.delete("/users/me", status_code=204)
async def handle_delete_users(
	cur_user: Annotated[UserEx01a, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
):
	session.delete(cur_user)
	session.commit()
	return Response(status_code=204)

# アイテムの追加
@app.post("/items")
async def handle_add_items(
	item: Item,
	cur_user: Annotated[UserEx01a, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	# データ型に変換し、user_idを付与
	db_item = ItemEx01a.model_validate(item)
	db_item.user_id = cur_user.id

	session.add(db_item)
	session.commit()
	session.refresh(db_item)
	return db_item

# ユーザーアイテムの全削除
@app.delete("/items", status_code=204)
async def handle_delete_items(
	cur_user: Annotated[UserEx01a, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
):
	# ループでitemを削除
	for item in cur_user.items:
		session.delete(item)
	session.commit()
	return Response(status_code=204)

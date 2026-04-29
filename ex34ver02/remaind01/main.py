"""
	### プロジェクトdirの環境構築から
	 - 依存関係ファイルの作成(pip freeze > requirements.txt)	- 完了
	 - 新規DBの作成(kimera:secret/ex34)							- 完了
	 - alembicのインストール									- 完了
	 - .envファイルの作成										- 完了

	### アプリの構築
	 - token											 - 完了
	 - user/register									 - 完了
	 - users=get										 - 完了
	 - users=delete										 - 完了
	 - items=post										 - 完了
	 - items=delete										 - 完了
	 - コードのレビュー									 - 修正から

	 - dockerイメージの作成								 -
	 - engineの記述(db:5433へ接続)						 -
	 - マイグレーションの作成(コンテナ内で実行)			 -



"""
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import create_engine, Session, select
from typing import Annotated
from pwdlib import PasswordHash
from datetime import datetime, timezone, timedelta
import jwt
from jwt.exceptions import InvalidTokenError
import os
from dotenv import load_dotenv

from models import User, UserResponse, UserDB, Item, ItemResponse, ItemDB, Token

dummy_hasher = PasswordHash.recommended()
KEY = os.environ("SECRET_KEY")
ALGORITHM = os.environ("ALGORITHM")
DUMMY = dummy_hasher.hash("dummy")
DATABASE = os.environ("DATABASE_URL")	# ymlファイルで設定した環境変数から取得

oauth2 = OAuth2PasswordBearer(tokenUrl="token")
load_dotenv()
app = FastAPI()
engine = create_engine(DATABASE)	# 後で入力

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

def get_cur_users(
	token: Annotated[str, Depends(oauth2)],
	session: Annotated[Session, Depends(get_session)]
) -> UserDB:
	error_detail = HTTPException(
		status_code=401,
		detail="Authentication failed",
		headers={"WWW-Authenticate": "Bearer"}
	)

	# トークンのデコード、ユーザー名の取得
	try:
		payload = jwt.decode(token, KEY, [ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise error_detail
	except InvalidTokenError:
		raise error_detail

	# ユーザーデータの取得
	statement = select(UserDB).where(UserDB.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		raise error_detail
	return db_user


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

# ユーザーの参照
@app.get("/users")
async def handle_get_users(
	cur_user: Annotated[UserDB, Depends(get_cur_users)]
) -> UserResponse:
	return cur_user

# ユーザー、ユーザーアイテムの削除
@app.delete("/users", status_code=204)
async def handle_delete_users(
	cur_user: Annotated[UserDB, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
):
	# ユーザーアイテム、ユーザーの削除
	for item in cur_user.items:
		session.delete(item)
	session.delete(cur_user)
	session.commit()
	return Response(status_code=204)

# ユーザーアイテムの追加
@app.post("/users/items")
async def handle_add_items(
	cur_user: Annotated[UserDB, Depends(get_cur_users)],
	item: Item,
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	db_item = ItemDB.model_validate(item)
	db_item.user_id = cur_user.id

	session.add(db_item)
	session.commit()
	session.refresh(db_item)
	return db_item

# ユーザーアイテムの削除
@app.delete("/users/items", status_code=204)
async def handle_delete_items(
	cur_user: Annotated[UserDB, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
):
	session.delete(cur_user.items)
	session.commit()
	return Response(status_code=204)

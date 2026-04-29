"""
	### 04-24: テストから

	### 環境構築
	 - 依存関係ファイルの作成(pip freeze > requirements.txt)	- 完了
	 - 新規DBの作成												- コンテナのテスト時に作成
	 - alembicのインストール									- 完了
	 - .envファイルの作成										- 完了
	 - .env.example作成											- 完了

	 - dockerfile, docker-composeの作成	 - 完了
	 - alembicの設定を修正				 - ここから
	 - alembic versionファイルを作成	 - コンテナのテスト時に作成
	 - conftest.pyの作成				 -
	 - test_main.pyの作成				 -
	 - dockerignoreの追加				 -
	 - アプリのテスト					 -


	### アプリの構築
	 - token				 - 完了
	 - users/register		 - 完了 認証無しで追加可能
	 - users=get(認証なし)	 - 完了
	 - users=delete			 - 完了
	 - items=get(認証なし)	 - 完了
	 - items/register=post	 - 完了
	 - items=delete			 - 完了



"""
from fastapi import FastAPI, Depends, HTTPException, Response, Path
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import Session, create_engine, select
from dotenv import load_dotenv
import os
from typing import Annotated
from pwdlib import PasswordHash
from datetime import datetime, timezone, timedelta
import jwt
from jwt.exceptions import InvalidTokenError

from models import User, Item, UserResponse, ItemResponse, UserDB, ItemDB, Token

load_dotenv()
app = FastAPI()
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

HASHER = PasswordHash.recommended()
DUMMY = HASHER.hash("dummy_hash")
DATABASE_URL = os.environ["DATABASE_URL"]
KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]

engine = create_engine(DATABASE_URL)

def get_session():
	with Session(engine) as session:
		yield session

def auth_users(
	username: str,
	password: str,
	session: Session
) -> UserDB | None:

	# ユーザーデータの取得
	statement = select(UserDB).where(UserDB.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		HASHER.verify(password, DUMMY)	# 疑似検証
		return None

	# ハッシュの検証
	if not HASHER.verify(password, db_user.password):
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

	# トークンをデコード
	try:
		payload = jwt.decode(token, KEY, [ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise error_detail
	except InvalidTokenError:
		raise error_detail

	# ユーザーデータを取得
	statement = select(UserDB).where(UserDB.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		raise error_detail
	return db_user

# トークンの発行
@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	session: Annotated[Session, Depends(get_session)]
) -> Token:

	# ユーザーの承認
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

	# 有効期限の設定、トークンの作成
	token_expire = timedelta(minutes=30)
	token = create_token(
		user_sub={"sub": db_user.username},
		token_expire=token_expire
	)
	return Token(
		access_token=token,
		token_type="Bearer"
	)

# ユーザーの追加(重複排除)
@app.post("/users/register")
async def handle_add_users(
	user: User,
	session: Annotated[Session, Depends(get_session)]
) -> UserResponse:

	# ユーザーDB型への変換
	db_user = UserDB.model_validate(user)

	# 既存ユーザーとの重複確認
	statement = select(UserDB).where(UserDB.username == db_user.username)
	in_db_user = session.exec(statement).first()
	if in_db_user:
		raise HTTPException(
			status_code=409,
			detail="Username is already used"
		)

	# パスのハッシュ化
	db_user.password = HASHER.hash(db_user.password)

	# ユーザーデータの保存
	session.add(db_user)
	session.commit()
	session.refresh(db_user)
	return db_user

# 保存されているユーザーデータの取得
@app.get("/users")
async def handle_all_users(
	session: Annotated[Session, Depends(get_session)]
) -> list[UserResponse]:

	db_users = session.exec(select(UserDB)).all()
	return db_users

# ユーザーの削除
@app.delete("/users", status_code=204)
async def handle_delete_users(
	cur_user: Annotated[UserDB, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
):
	# ユーザーアイテムの削除
	for item in cur_user.items:
		session.delete(item)

	session.delete(cur_user)
	session.commit()
	return Response(status_code=204)

# ユーザーアイテムの追加
@app.post("/items/register")
async def handle_add_items(
	item: Item,
	cur_user: Annotated[UserDB, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:

	# アイテムDB型に変換
	db_item = ItemDB.model_validate(item)

	# アイテム名の重複を確認
	statement = select(ItemDB).where(ItemDB.name == db_item.name)
	in_db_item = session.exec(statement).first()
	if in_db_item:
		raise HTTPException(
			status_code=409,
			detail="Item name is already used"
		)

	# ユーザーIDの付与
	db_item.user_id = cur_user.id

	# データの保存
	session.add(db_item)
	session.commit()
	session.refresh(db_item)
	return db_item

# ユーザーアイテムの参照(認証なし)
@app.get("/items")
async def handle_all_items(
	session: Annotated[Session, Depends(get_session)]
) -> list[ItemResponse]:

	db_items = session.exec(select(ItemDB)).all()
	return db_items

@app.delete("/items/{id}", status_code=204)
async def handle_delete_items(
	id: Annotated[int, Path(ge=1)],
	cur_user: Annotated[UserDB, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
):
	# アイテムデータの取得
	db_item = session.get(ItemDB, id)
	if not db_item:
		raise HTTPException(
			status_code=404,
			detail="Item not found"
		)

	# ユーザー所有のアイテムか確認
	if not db_item.user_id == cur_user.id:
		raise HTTPException(
			status_code=403,
			detail="Not authorized"
		)

	# アイテムの削除
	session.delete(db_item)
	session.commit()
	return Response(status_code=204)

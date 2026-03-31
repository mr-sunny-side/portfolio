"""
	アプリの構築	- マイグレーション作成から
	- Token		- 完了
	- user/add	- 完了
	- users/me=delete	- 完了
	- users/me			- 完了
	- items=post, items=delete	- 完了
	マイグレーションの作成


"""
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, create_engine, select
from typing import Annotated
from pwdlib import PasswordHash
from datetime import datetime, timezone, timedelta
import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv
import os

from models import Token, User, Item, UserResponse, ItemResponse, UserEx01, ItemEx01

app = FastAPI()
engine = create_engine("postgresql://ex33:secret@localhost/ex33_db")
oauth2 = OAuth2PasswordBearer(tokenUrl="token")
dummy_hasher = PasswordHash.recommended()
load_dotenv()

DUMMY = dummy_hasher.hash("dummy")
KEY = os.environ("SECRET_KEY")
ALGORITHM = os.environ("ALGORITHM")

def get_session():
	with Session(engine) as session:
		yield session

def auth_users(
	form_data: OAuth2PasswordRequestForm,
	session: Session
) -> UserEx01 | None:
	hasher = PasswordHash.recommended()

	# ユーザーデータの取り出し
	statement = select(UserEx01).where(UserEx01.username == form_data.username)
	db_user = session.exec(statement).first()
	if not db_user:
		hasher.verify(form_data.password, DUMMY)
		return None

	# パスワードの検証
	if not hasher.verify(form_data.password, db_user.password):
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
	session: Annotated[Session, Depends(get_session)],
	token: Annotated[str, Depends(oauth2)]
) -> UserEx01:
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

	# ユーザーの検索
	statement = select(UserEx01).where(UserEx01.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		raise error_detail
	return db_user



@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	session: Annotated[Session, Depends(get_session)]
) -> Token:

	# ユーザーの認証
	db_user = auth_users(form_data, session)
	if not db_user:
		raise HTTPException(
			status_code=401,
			detail="Authentication failed",
			headers={"WWW-Authenticate": "Bearer"}
		)

	# トークンの作成
	token_expire = timedelta(minutes=30)
	token = create_token(
		user_sub={"sub": form_data.username},
		token_expire=token_expire
	)

	return Token(
		access_token=token,
		token_type="Bearer"
	)

@app.post("/users/add")
async def handle_add_users(
	user: User,
	session: Annotated[Session, Depends(get_session)]
) -> UserResponse:
	hasher = PasswordHash.recommended()

	# db型への変換、パスワードのハッシュ化
	db_user = UserEx01.model_validate(user)
	db_user.password = hasher.hash(db_user.password)

	session.add(db_user)
	session.commit()
	session.refresh(db_user)
	return db_user

@app.delete("/users/me", status_code=204)
async def handle_delete_users(
	cur_users: Annotated[UserEx01, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
):
	session.delete(cur_users)
	session.commit()
	return Response(status_code=204)

@app.get("/users/me")
async def handle_all_users(
	session: Annotated[Session, Depends(get_session)]
) -> list[UserResponse]:
	db_users = session.exec(select(UserEx01)).all()
	return db_users

@app.post("/items")
async def handle_add_items(
	item: Item,
	cur_user: Annotated[UserEx01, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	# db型への変換、外部キーの付与
	db_item = ItemEx01.model_validate(item)
	db_item.user_id = cur_user.id

	session.add(db_item)
	session.commit()
	session.refresh(db_item)
	return db_item

@app.delete("/items", status_code=204)
async def handle_delete_items(
	cur_user: Annotated[UserEx01, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
):
	# ユーザーのitem情報をループして削除
	for item in cur_user.items:
		session.delete(item)
	session.commit()
	return Response(status_code=204)

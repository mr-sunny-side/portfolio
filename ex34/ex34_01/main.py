"""
	03-18:	マイグレーションの作成、テストから
			- 新しいdbの作成
			- マイグレーション作成

			アプリの構築 - 完了
			- user/register, users/me=delete, users/me/items
			- items=post, items=delete
			マイグレーションの作成	- 完了
			dockerイメージの作成	- 完了

			ex34_01の復習から(全部書き直す)
			アプリの作成

"""
from fastapi import FastAPI, Depends, HTTPException, Response, Path
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated
from sqlmodel import Session, create_engine, select
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv
import os

from ex34_01.models import Token, User, Item, UserResponse, ItemResponse, UserEx01, ItemEx01
# appから見て相対的な場所を指定

load_dotenv()
dummy_hasher = PasswordHash.recommended()
app = FastAPI()
engine = create_engine("postgresql://ex33:secret@localhost/ex33_db")
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

DUMMY = dummy_hasher.hash("dummy")
KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def get_session():
	with Session(engine) as session:
		yield session

def auth_user(
	username: str,
	password: str,
	session: Session
) -> UserEx01 | None:
	hasher = PasswordHash.recommended()

	statement = select(UserEx01).where(UserEx01.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		hasher.verify(password, DUMMY)	# 疑似検証
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
		expire =datetime.now(timezone.utc) + timedelta(minutes=30)

	copy_sub.update({"exp": expire})
	token = jwt.encode(copy_sub, KEY, ALGORITHM)
	return token

def get_cur_user(
	token: Annotated[str, Depends(oauth2)],
	session: Annotated[Session, Depends(get_session)]
) -> UserEx01:
	error_detail = HTTPException(
		status_code=401,
		detail="Authentication failed",
		headers={"WWW-Authenticate": "Bearer"}
	)

	try:
		payload = jwt.decode(token, KEY, [ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise error_detail
	except InvalidTokenError:
		raise error_detail

	statement = select(UserEx01).where(UserEx01.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		raise error_detail
	return db_user


@app.post("/users/register")
async def handle_users_register(
	user: User,
	session: Annotated[Session, Depends(get_session)]
) -> UserResponse:
	hasher = PasswordHash.recommended()

	db_user = UserEx01.model_validate(user)
	db_user.password = hasher.hash(db_user.password)	# パスをハッシュ化して保存

	session.add(db_user)
	session.commit()
	session.refresh(db_user)
	return db_user

@app.get("/users/me")
async def handle_all_users(
	session: Annotated[Session, Depends(get_session)]
) -> list[UserResponse]:
	db_users = session.exec(select(UserEx01)).all()
	return db_users

@app.delete("/users/me", status_code=204)
async def handle_delete_users(
	cur_user: Annotated[UserEx01, Depends(get_cur_user)],
	session: Annotated[Session, Depends(get_session)]
):
	session.delete(cur_user)
	session.commit()
	return Response(status_code=204)

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	session: Annotated[Session, Depends(get_session)]
) -> Token:
	# ユーザー認証、データの取り出し
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

	# トークン作成
	token_expire = timedelta(minutes=30)
	token = create_token(
		user_sub={"sub": db_user.username},
		token_expire=token_expire
	)

	return Token(
		access_token=token,
		token_type="Bearer"
	)

@app.post("/items")
async def handle_add_items(
	item: Item,
	cur_user: Annotated[UserEx01, Depends(get_cur_user)],
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	db_item = ItemEx01.model_validate(item)
	db_item.user_id = cur_user.id
	session.add(db_item)
	session.commit()
	session.refresh(db_item)
	return db_item

@app.delete("/items/{id}", status_code=204)
async def handle_delete_items(
	id: Annotated[int, Path(ge=1)],
	cur_users: Annotated[UserEx01, Depends(get_cur_user)],
	session: Annotated[Session, Depends(get_session)]
):
	statement = select(ItemEx01).where(UserEx01.id == id)
	db_item = session.exec(statement).first()
	if not db_item:
		raise HTTPException(
			status_code=404,
			detail="Item not found"
		)

	session.delete(db_item)
	session.commit()
	return Response(status_code=204)

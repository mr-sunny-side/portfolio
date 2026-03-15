"""
	03-14:	DBの実装	- 完了
			トークンの実装	- 完了
			alembicの設定変更	- crete_allの削除から

"""
from fastapi import FastAPI, Depends, Path, HTTPException, Response
from sqlmodel import SQLModel, create_engine, Session, select, Field
from pydantic import BaseModel, Field
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv
import os

from model import Item, ItemResponse, ItemEx06, User, UserResponse, UserEx06, \
	Token, TokenData

# engine(DBの窓口)の作成
engine = create_engine("postgresql://ex33:secret@localhost/ex33_db")

## DBの設定
# スタートアップ後の制御を委譲
app = FastAPI()
load_dotenv()
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def get_session():
	with Session(engine) as session:
		yield session

def auth_user(
	username: str,
	password: str,
	session: Annotated[Session, Depends(get_session)]
) -> UserEx06 | None:

	hasher = PasswordHash.recommended()

	# DB検索のコマンド、ユーザーの捜索
	statement = select(UserEx06).where(UserEx06.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		return None

	# パスワードの確認
	if not hasher.verify(password, db_user.hashed_password):
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
		expire = datetime.now(timezone.utc) + timedelta(minutes=15)

	# トークンの作成
	copy_sub.update({"exp": expire})
	token = jwt.encode(copy_sub, key=KEY, algorithm=ALGORITHM)
	return token

def get_cur_user(
	token: Annotated[str, Depends(oauth2)],
	session: Annotated[Session, Depends(get_session)]
) -> UserEx06:
	error_detail = HTTPException(
		status_code=401,
		detail="Authentication failed",
		headers={"WWW-Authenticate": "Bearer"}
	)

	try:
		# トークンをデコード
		payload = jwt.decode(token, key=KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise error_detail
	except InvalidTokenError:
		raise error_detail

	# 取得したusernameを検索
	statement = select(UserEx06).where(UserEx06.username == username)
	db_user = session.exec(statement).first()
	if not db_user:
		raise error_detail
	return db_user

# Item追加
@app.post("/items")
async def handle_add_items(
	item: Item,
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	db_item = ItemEx06.model_validate(item)
	session.add(db_item)
	session.commit()
	session.refresh(db_item)
	return db_item

# ItemDBの全件取得
@app.get("/items")
async def handle_all_items(
	session: Annotated[Session, Depends(get_session)]
) -> list[ItemResponse]:
	items = session.exec(select(ItemEx06)).all()
	return items

@app.get("/items/{id}")
async def handle_one_items(
	id: Annotated[int, Path(ge=1)],
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	item = session.get(ItemEx06, id)
	if not item:
		raise HTTPException(
			status_code=404,
			detail="Item not found"
		)

	return item

@app.put("/items/{id}")
async def handle_change_items(
	id: Annotated[int, Path(ge=1)],
	item: Item,
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	db_item = session.get(ItemEx06, id)
	if not db_item:
		raise HTTPException(
			status_code=404,
			detail="Item not found"
		)

	db_item.name = item.name
	db_item.price = item.price

	session.add(db_item)
	session.commit()
	session.refresh(db_item)
	return db_item

@app.delete("/items/{id}", status_code=204)
async def handle_delete_items(
	id: Annotated[int, Path(ge=1)],
	session: Annotated[Session, Depends(get_session)]
):
	db_item = session.get(ItemEx06, id)
	if not db_item:
		raise HTTPException(
			status_code=404,
			detail="Item not found"
		)

	session.delete(db_item)
	session.commit()
	return Response(status_code=204)

@app.post("/users/register")
async def handle_add_users(
	user: User,
	session: Annotated[Session, Depends(get_session)]
) -> UserResponse:
	# 平文パスワードをハッシュ化
	hasher = PasswordHash.recommended()
	user.hashed_password = hasher.hash(user.hashed_password)

	# DBに変換
	db_user = UserEx06.model_validate(user)
	session.add(db_user)
	session.commit()
	session.refresh(db_user)
	return db_user

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	session: Annotated[Session, Depends(get_session)]
) -> Token:

	# 依存性の自動注入はエンドポイントだけ
	user = auth_user(
		form_data.username,
		form_data.password,
		session
	)

	# 認証に失敗なら401
	if not user:
		raise HTTPException(
			status_code=401,
			detail="Incorrect username or password"
		)

	# トークンの作成、有効期限の設定
	token_expire = timedelta(minutes=30)
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
	user: Annotated[UserResponse, Depends(get_cur_user)]
) -> UserResponse:
	return user

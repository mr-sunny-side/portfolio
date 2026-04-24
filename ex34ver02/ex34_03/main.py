"""
	### プロジェクトdirの環境構築から
	 - 依存関係ファイルの作成(pip freeze > requirements.txt)	-
	 - 新規DBの作成(kimera:secret/ex34)							-
	 - alembicのインストール									-
	 - .envファイルの作成										-

	### アプリの構築
	 - token				 - 完了
	 - user/register		 - 完了
	 - users=get(認証なし)	 - 完了
	 - users=delete			 - 完了
	 - items=post			 - 完了
	 - items=delete			 - 完了
	 - コードのレビュー		 -


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

HASHER = PasswordHash.recommended()
DUMMY = HASHER.hash("dummy")
DATABASE_URL = os.environ["DATABASE_URL"]
KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]

app = FastAPI()
engine = create_engine(DATABASE_URL)
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

def get_session():
	with Session(engine) as session:
		yield session

def auth_users(
	username: str,
	password: str,
	session: Session
) -> UserDB | None:

	# ユーザーの取得
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

	# 有効期限の設定
	if token_expire:
		expire = datetime.now(timezone.utc) + token_expire
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=30)

	# トークンの作成
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

	# トークンのデコード
	try:
		payload = jwt.decode(token, KEY, [ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise error_detail
	except InvalidTokenError:
		raise error_detail

	# ユーザー情報の取得
	statement = select(UserDB).where(UserDB.username == username)
	db_user = session.exec(statement).first()
	return db_user

# トークンの発行
@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	session: Annotated[Session, Depends(get_session)]
) -> Token:

	# ユーザーの認証
	db_user = auth_users(
		form_data.username,
		form_data.password,
		session
	)
	if not db_user:
		raise HTTPException(
			status_code=401,
			detail="Authentication failed",
			headers={"WWW-Authenticate": "Bearer"} # authenticate...本人確認する
		)

	# 有効期限の設定
	token_expire = timedelta(minutes=30)

	# トークンの作成
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

	# ユーザーDB型に変換、パスをハッシュ化
	db_user = UserDB.model_validate(user)
	db_user.password = HASHER.hash(db_user.password)

	# DBに保存
	session.add(db_user)
	session.commit()
	session.refresh(db_user)
	return db_user

# 全ユーザーの参照（認証なし）
@app.get("/users")
async def handle_get_users(
	session: Annotated[Session, Depends(get_session)]
) -> list[UserResponse]:

	db_users = session.exec(select(UserDB)).all()
	return db_users

# ユーザーデータの削除
@app.delete("/users", status_code=204)
async def handle_delete_users(
	cur_user: Annotated[UserDB, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
):

	# ユーザーアイテムの削除
	for item in cur_user.items:
		session.delete(item)

	# ユーザーの削除
	session.delete(cur_user)
	session.commit()
	return Response(status_code=204)

# ユーザーアイテムの追加
@app.post("/items")
async def handle_add_items(
	item: Item,
	cur_user: Annotated[UserDB, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:

	# アイテムDB型への変換、ユーザーIDの付与
	db_item = ItemDB.model_validate(item)
	db_item.user_id = cur_user.id

	# DBへ保存
	session.add(db_item)
	session.commit()
	session.refresh(db_item)
	return db_item

# ユーザーアイテムの削除
@app.delete("/items/{id}", status_code=204)
async def handle_delete_items(
	id: Annotated[int, Path(ge=1)],
	cur_user: Annotated[UserDB, Depends(get_cur_users)],
	session: Annotated[Session, Depends(get_session)]
):
	# 指定IDのアイテムを取得
	db_item = session.get(ItemDB, id)
	if not db_item:
		raise HTTPException(
			status_code=404,
			detail="Item not found"
		)

	# ユーザー保有のアイテムか確認
	if not db_item.user_id == cur_user.id:
		raise HTTPException(
			status_code=403,
			detail="Not authorized"	# authorize...許可する
		)

	session.delete(db_item)
	session.commit()
	return Response(status_code=204)

"""
	03-09:	テストから

"""
from fastapi import FastAPI, Depends, HTTPException, Path, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated
from pydantic import BaseModel
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import jwt
from jwt.exceptions import InvalidTokenError
from sqlmodel import SQLModel, create_engine, Field, Session, select
from contextlib import asynccontextmanager

fake_users_db = {
	"johndoe": {
		"username": "johndoe",
		"full_name": "John Doe",
		"email": "johndoe@example.com",
		"hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
		"disabled": False,
	}
}

class User(BaseModel):
	username: str
	full_name: str | None = None
	email: str | None = None
	disabled: bool | None = None

class UserInDB(User):
	hashed_password: str

class Token(BaseModel):
	access_token: str
	token_type: str

class TokenData(BaseModel):
	username: str

# クライアントから受け取るItem型
class Item(BaseModel):
	name: str
	price: int = Field(ge=0)

# DBのItem型
class ItemEx04(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	name: str = Field(index=True)
	price: int

class ItemResponse(BaseModel):
	id: int
	name: str
	price: int

# engine(DBの窓口)を作成
engine = create_engine("postgresql://ex33:secret@localhost/ex33_db")

# テーブルを作成する関数
def create_db():
	SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):	# asyncである必要がある
	create_db()						# 終了処理のためにyieldが必要
	yield

app = FastAPI(lifespan=lifespan)	# 開始・終了のタイミングを委譲する(lifespan)
load_dotenv()
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

DUMMY_HASH = "dummyhash"
KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def get_session():
	with Session(engine) as session:
		yield session

def auth_user(
	fake_db, username: str, password: str
) -> UserInDB | None:

	# ハッシュ関係のインスタンスを取得
	hasher = PasswordHash.recommended()

	# ユーザーが存在するか確認
	if username not in fake_db:
		hasher.verify(password, DUMMY_HASH)	# 疑似検証でタイミング剛撃対策
		return None

	# ユーザー情報を取得、ハッシュを検証
	user = UserInDB(**fake_db[username])
	if not hasher.verify(password, user.hashed_password):
		return None
	return user

def create_token(
	user_sub: dict,
	token_expire: timedelta | None = None
):
	# 作業用にsubをコピー
	token_sub = user_sub.copy()

	#有効期限を設定
	if token_expire:
		expire = datetime.now(timezone.utc) + token_expire
	else:
		expire =datetime.now(timezone.utc) + timedelta(minutes=15)

	# トークンの作成
	token_sub.update({"exp": expire})
	token = jwt.encode(token_sub, key=KEY, algorithm=ALGORITHM)
	return token

def get_cur_user(
	token: Annotated[str, Depends(oauth2)]
) -> UserInDB:

	# トークンの検証、ユーザーの照合エラーの型
	error_detail = HTTPException(
		status_code=401,
		detail="Authentication failed",
		headers={"WWW-Authenticate": "Bearer"}
	)

	# トークンをデコードしてusernameを取り出す
	try:
		payload = jwt.decode(token, key=KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise error_detail
		token_data = TokenData(username=username)
	except InvalidTokenError:
		raise error_detail

	# usernameからデータを探す、無ければエラー
	if token_data.username not in fake_users_db:
		raise error_detail
	user = UserInDB(**fake_users_db[token_data.username])
	return user

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
	# ユーザー認証
	user = auth_user(
		fake_users_db,
		form_data.username,
		form_data.password
	)

	# 認証できなければエラー
	if not user:
		raise HTTPException(
			status_code=401,
			detail="Incorrect username or password",
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

@app.get("/users/me")
async def handle_me(
	cur_user: Annotated[User, Depends(get_cur_user)]
) -> User:
	return cur_user

@app.post("/items")
async def handle_add_items(
	item: Item,
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	db_item = ItemEx04.model_validate(item)
	session.add(db_item)
	session.commit()
	session.refresh(db_item)
	return db_item

@app.get("/items")
async def handle_all_items(
	session: Annotated[Session, Depends(get_session)]
) -> list[ItemResponse]:
	items = session.exec(select(ItemEx04)).all()
	return items

@app.get("/items/{id}")
async def handle_one_items(
	id: Annotated[int, Path(ge=1)],
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	db_item = session.get(ItemEx04, id)
	if not db_item:
		raise HTTPException(
			status_code=404,
			detail="Item not found"
		)
	return db_item

@app.put("/items/{id}")
async def handle_change_items(
	id: Annotated[int, Path(ge=1)],
	item: Item,
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	db_item = session.get(ItemEx04, id)
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

@app.delete("/items/{id}")
async def handle_delete_items(
	id: Annotated[int, Path(ge=1)],
	session: Annotated[Session, Depends(get_session)]
):
	db_item = session.get(ItemEx04, id)
	if not db_item:
		raise HTTPException(
			status_code=404,
			detail="Item not found"
		)

	session.delete(db_item)
	session.commit()
	return Response(status_code=204)

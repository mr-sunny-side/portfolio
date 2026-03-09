"""
	03-08:	レビューを見て修正から
			- notionの実装例も変更

"""
from fastapi import FastAPI, Depends, HTTPException, Path
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

# db関係のスタートアップの記述
@asynccontextmanager
async def lifespan(app: FastAPI):
	create_db()
	yield

load_dotenv()
app = FastAPI(lifespan=lifespan)	# データベースの開閉のタイミングを委譲する
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

# postgreSQLのエンジン(dbとの架け橋)を作成
engine = create_engine("postgresql://ex33:secret@localhost/ex33_db")

DUMMY_HASH = "dummyhash"
TOKEN_EXPIRE = 30
KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


fake_users_db = {
	"johndoe": {
		"username": "johndoe",
		"full_name": "John Doe",
		"email": "johndoe@example.com",
		"hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
		"disabled": False,
	}
}

# クライアントに渡すトークンの型
class Token(BaseModel):
	access_token: str
	token_type: str

# デコードしたトークンから情報を取り出す用の型
class TokenData(BaseModel):
	username: str

# クライアントに渡すユーザー情報型
class User(BaseModel):
	username: str
	full_name: str | None = None
	email: str | None = None
	disabled: bool | None = None

# DBで管理するハッシュありユーザー情報型
class UserInDB(User):
	hashed_password: str

# クライアントからの受取用、Item型
class Item(BaseModel):
	name: str
	price: int = Field(ge=0)

# DB管理用のItem型
class ItemInDB(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	name: str = Field(index=True)
	price: int

# レスポンス用のItem型
class ItemResponse(BaseModel):
	id: int
	name: str
	price: int

def auth_user(
	fake_db, username: str, password: str
) -> UserInDB | None:
	hasher = PasswordHash.recommended()

	# ユーザーの存在を確認
	if username not in fake_db:
		hasher.verify(password, DUMMY_HASH)
		return None

	# ユーザー情報を取得
	user = UserInDB(**fake_db[username])

	# パスの検証
	if not hasher.verify(password, user.hashed_password):
		return None
	return user

def create_token(
	user_sub: dict,
	token_expire: timedelta | None = None
) -> str:
	# 戻り値のためのsubをコピー作成
	response = user_sub.copy()

	# 有効期限を設定
	if token_expire:
		expire = datetime.now(timezone.utc) + token_expire
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=15)

	# トークンを作成
	response.update({"exp": expire})
	encoded = jwt.encode(response, KEY, algorithm=ALGORITHM)
	return encoded

def	get_cur_user(
	token: Annotated[str, Depends(oauth2)]
) -> UserInDB:
	"""
	# JWTトークンをデコードして認証を確認する関数

	1. トークンのデコード
	2. デコードしたトークンからusernameを取得
	3. TokenDataインスタンスとしてユーザー名を取得
	4. dbに存在するか確認し、UserInDBインスタンスに変換
	5. インスタンスをreturn

	"""
	error_detail = HTTPException(
		status_code=401,
		detail="Authentication failed",
		headers={"WWW-Authenticate": "Bearer"}
	)

	try:
		payload = jwt.decode(token, KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise error_detail
		token_data = TokenData(username=username)
	except InvalidTokenError:
		raise error_detail

	# DBからユーザー情報を取得、無ければエラー
	if token_data.username not in fake_users_db:
		raise error_detail

	user = UserInDB(**fake_users_db[token_data.username])
	return user

def create_db():
	SQLModel.metadata.create_all(engine)

def get_session():
	with Session(engine) as session:
		yield session

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
	"""
	1. authenticate_userで、ユーザーの存在・ハッシュの一致を確認
		- ユーザーデータを取得
		- 存在しないなら401
	2. create_tokenでJWTトークンを作成
		- timedeltaで有効期限を設定
	3. Tokenインスタンスをレスポンス

	"""
	# ユーザーの存在、パスの一致を検証
	user = auth_user(fake_users_db, form_data.username, form_data.password)
	if not user:
		raise HTTPException(
			status_code=401,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"}
		)

	# expire期間を定義し、トークンを作成
	token_expire = timedelta(minutes=TOKEN_EXPIRE)
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
	cur_user: Annotated[User, Depends(get_cur_user)]
) -> User:
	return cur_user

@app.post("/items")
async def handle_add_items(
	item: Item,
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	# DB用のprimary_keyがあるデータに変換
	db_item = ItemInDB.model_validate(item)
	session.add(db_item)
	session.commit()
	session.refresh(db_item)
	return db_item

@app.get("/items")
async def handle_all_items(
	session: Annotated[Session, Depends(get_session)]
) -> list[ItemResponse]:
	# select * from ItemInDBで取得したデータをすべて出力
	items = session.exec(select(ItemInDB)).all()
	return items

@app.get("/items/{id}")
async def handle_one_items(
	id: Annotated[int, Path(ge=1)],
	session: Annotated[Session, Depends(get_session)]
) -> ItemResponse:
	# 指定のIDのItemを取得
	item = session.get(ItemInDB, id)
	if not item:
		raise HTTPException(
			status_code=404,
			detail="Item not found"
		)
	return item

"""
	02-24: テストの実装から

"""

from fastapi import FastAPI, Query, Path, Depends, HTTPException
from typing import Annotated
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, create_engine, Session, select

app = FastAPI()

# dbのファイル名を指定
# エンジン(dbを開くオブジェクト)の作成
db_url = "sqlite:///ex31_06.db"
engine = create_engine(db_url, connect_args={"check_same_thread": False})

# 基礎となるデータベースの型
class ItemBase(SQLModel):
	name: str = Field(min_length=1)
	price: int = Field(ge=0)
	tax: float = Field(default=0, ge=0)

# DB用
class ItemDB(ItemBase, table=True):
	id: int | None = Field(default=None, primary_key=True)

# ユーザーから受け取る用
class ItemGet(ItemBase):
	pass

# クライアントへのレスポンス用
class ItemResponse(ItemBase):
	id: int

# セッションを作成し、closeまで担当する関数
async def get_session():
	with Session(engine) as session:
		yield session
	# with文から抜けたら自動でクローズ
	# yieldでセッションを返して一時停止する

@app.get("/")
async def handle_index():
	return {"message": "Hello FastAPI !"}

@app.get("/echo/{text}")
async def handle_echo(text: Annotated[str, Path(min_length=1)]):
	return {"echo": text}

@app.post("/items", response_model=ItemResponse, status_code=201)
async def handle_add_items(
	item: ItemGet,
	session: Annotated[Session, Depends(get_session)]	# セッションを関数ありきで呼び出す
):
	db_item = ItemDB.model_validate(item)	# ItemDBに変換する(table=Trueがあるもののみ可能)
	session.add(db_item)
	session.commit()
	session.refresh(db_item)				# idがついた状態のdb_itemを取得
	return db_item


@app.get("/items", response_model=list[ItemResponse])
async def handle_all_items(session: Annotated[Session, Depends(get_session)]):
	return session.exec(select(ItemDB)).all()
	# select * from ItemDB == session.exec(select(ItemDB))
	# all()でDBから取得したデータのすべてを、リストとして取り出す

@app.get("/items/{id}", response_model=ItemResponse)
async def handle_one_items(
	id: Annotated[int, Path(ge=1)],
	session: Annotated[Session, Depends(get_session)]
):
	item = session.get(ItemDB, id)	# 指定IDのitemをDBから取り出し
	if not item:
		raise HTTPException(status_code=404, detail="Item not found")
	return item

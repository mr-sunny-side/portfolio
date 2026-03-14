"""
	03-14:	DBの実装	- 完了
			トークンの実装
			alembicの設定変更

"""
from fastapi import FastAPI, Depends, Path, HTTPException, Response
from sqlmodel import SQLModel, create_engine, Session, select
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from typing import Annotated

# engine(DBの窓口)の作成
engine = create_engine("postgresql://ex33:secret@localhost/ex33_db")

## DBの設定
# テーブルの作成関数
def create_table():
	SQLModel.metadata.create_all(engine)

# スタートアップ時の動作設定
@asynccontextmanager
async def lifespan(app: FastAPI):
	create_table()
	yield

# スタートアップ後の制御を委譲
app = FastAPI(lifespan=lifespan)

# クライアントからの受取用型
class Item(BaseModel):
	name: str
	price: int = Field(ge=0)

# レスポンス用Item型
class ItemResponse(Item):
	id: int

class ItemEx06(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	name: str
	price: int

def get_session():
	with Session(engine) as session:
		yield session

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

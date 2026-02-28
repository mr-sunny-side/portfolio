"""
	02-27:	- 06の復習
			- PUT, DELETEの追加

"""
from typing import Annotated
from fastapi import FastAPI, Path, Query, Depends, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select

app = FastAPI()

# dbのファイル名
# 複数スレッドでの仕様を許可し、engine(dbの窓口)を作成
db_url = "sqlite:///ex31_06a.db"
engine = create_engine(db_url, connect_args={"check_same_thread": False})

class ItemBase(SQLModel):
	name: str = Field(min_length=1)
	price: int = Field(ge=0)
	tax: float = Field(default=0, ge=0)

class ItemAdd(ItemBase):
	pass

class ItemDB(ItemBase, table=True):
	id: int | None = Field(default=None, primary_key=True)

class ItemResponse(ItemBase):
	id: int

SQLModel.metadata.create_all(engine)

async def get_session():
	with Session(engine) as session:
		yield session

@app.get("/")
async def handle_index():
	return {"message": "Hello FastAPI !"}

@app.get("/echo/{text}")
async def handle_echo(text: str):
	return {"echo": text}

@app.post("/items", response_model=ItemResponse, status_code=201)
async def handle_add_items(
	item: ItemAdd,
	session: Annotated[Session, Depends(get_session)]
):
	item = ItemDB.model_validate(item)	# itemDBに変換
	session.add(item)
	session.commit()
	session.refresh(item)
	return item

@app.get("/items", response_model=list[ItemResponse])
async def handle_all_items(
	session: Annotated[Session, Depends(get_session)]
):
	return session.exec(select(ItemDB)).all()	# dbから全カラムを取り出し、全件pythonリストに変換

@app.get("/items/{id}", response_model=ItemResponse)
async def handle_one_items(
	id: Annotated[int, Path(ge=1)],
	session: Annotated[Session, Depends(get_session)]
):
	item = session.get(ItemDB, id)
	if not item:
		raise HTTPException(status_code=404, detail="Item not found")
	return item

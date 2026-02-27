"""
	02-27:	- 06の復習
			- PUT, DELETEの追加

"""
from typing import Annotated
from fastapi import FastAPI, Path, Query, Depends
from sqlmodel import SQLModel, Field, create_engine, Session

app = FastAPI()

# dbのファイル名
# 複数スレッドでの仕様を許可し、engine(dbの窓口)を作成
db_url = "sqlite:///ex31_06a.py"
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

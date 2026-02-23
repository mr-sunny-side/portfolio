"""
	02-23: pytestを書くところから

"""

from fastapi import FastAPI, Query, Path
from pydantic import BaseModel, Field
from typing import Annotated

app = FastAPI()
item_id = 1
items = []

# 列挙型への変更
class Item(BaseModel):
	name: str = Field(min_length=1)
	price: int = Field(ge=0)
	tax: float = Field(default=0, ge=0)

class ItemResponse(BaseModel):
	id: int = Field(ge=1)
	name: str = Field(min_length=1)
	price: int = Field(ge=0)
	tax: float = Field(default=0, ge=0)

@app.get("/")
async def handle_index():
	return {"message": "Hello FastAPI !"}

@app.get("/echo/{text}")
async def handle_echo(
	text: Annotated[int, Path(min_length=1)]
):
	return {"echo": text}

@app.post("/items", response_model=ItemResponse)
async def handle_add_items(item: Item):
	global item_id

	item_dict = item.model_dump()
	item_dict.update({"id": item_id})
	items.append(item_dict)
	item_id += 1
	return item_dict

@app.get("/items", response_model=list[ItemResponse])
async def handle_all_items():
	return items

@app.get("/items/{id}", response_model=ItemResponse)
async def handle_one_items(
	id: Annotated[int, Path(ge=1)]
):
	item = next((i for i in items if i["id"] == id), None)
	return item

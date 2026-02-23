from fastapi import FastAPI, Query, Path
from typing import Annotated
from pydantic import BaseModel, Field

app = FastAPI()
items = []
item_id = 1

class Item(BaseModel):
	name	: str = Field(min_length=1)
	price	: int = Field(ge=0)
	tax		: float = Field(default=0, ge=0)

@app.get("/")
async def	handle_index():
	return {"message": "Hello FastAPI !"}

@app.get("/echo/{text}")
async def	handle_echo(text: Annotated[str, Path(min_length=1)]):
	return {"echo": text}

@app.post("/items")
async def	handle_add_items(item: Item):
	global item_id

	item_dict = item.model_dump()
	item_dict.update({"id": item_id})
	items.append(item_dict)
	item_id += 1
	return item_dict

@app.get("/items")
async def	handle_all_items(
	skip: Annotated[int, Query(ge=0)] = 0,
	limit: Annotated[int, Query(ge=1, le=100)] = 10
):
	return items[skip : skip + limit]

@app.get("/items/{id}")
async def	handle_one_items(
	id: Annotated[int, Path(ge=1)]
):
	item = next((i for i in items if i["id"] == id), None)
	if not item:
		return {"message": "Item not found"}
	return item

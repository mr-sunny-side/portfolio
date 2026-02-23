"""
	02-22:	クエリパラメータ、リクエストボディを読むところから
			- クエリパラメータの実装
			- リクエストボディを読んで実装

			保存する際はmodel_dumpで辞書化してから保存

"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
item_id = 0
items = []

class	Item(BaseModel):
	name: str
	price: int
	tax: float | None = None

@app.get("/")
async def	handle_index():
	return	{"message": "Hello FastAPI !"}

@app.get("/echo/{text}")
async def	handle_echo(text):
	return	{"echo": text}

@app.post("/items")
async def	add_items(item: Item):
	global	item_id

	item_dict = item.model_dump()	# 辞書に変換
	item_dict['id'] = item_id		# idの付与
	items.append(item_dict)
	item_id += 1
	return	item_dict

@app.get("/items")
async def	all_items(skip: int = 0, limit: int = 10):	#デフォルト値を設定して、入力なしに対応
	return	items[skip : skip + limit]					# limitは表示する件数なので加算する

@app.get("/items/{id}")
async def	one_items(id: int):
	# noneでデフォルト値を設定、無いと例外が発生する
	item = next((i for i in items if i['id'] == id), None)
	if not item:
		return {"message": "Item not found"}
	return item

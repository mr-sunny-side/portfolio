"""
	02-21: Enumクラスの理解から(ex自体は完了)

"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def	handle_index():
	return {"message": "Hello FastAPI!"}

@app.get("/ping")
async def	handle_ping():
	return {"status": "ok"}

@app.get("/echo/{text}")
async def	handle_echo(text: str):
	return {"echo": text}

# /items/idではエラーになるので、先に宣言されている必要がある
@app.get("/items/me")
async def	handle_me():
	return {"item_id": "me"}

@app.get('/items/{id}')
async def	handle_items(id: int):
	return {"item_id": id}

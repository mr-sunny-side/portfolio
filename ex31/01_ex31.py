"""
	02-21: 事前解説を読むところから

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
async def	handle_echo(text):
	return {"echo": text}

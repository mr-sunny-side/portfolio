"""
	02-27:	- 06の復習
			- PUT, DELETEの追加

"""
from typing import Annotated
from fastapi import FastAPI, Path, Query
from sqlmodel import SQLModel, Field, create_engine,

app = FastAPI()

@app.get("/")
async def handle_index():
	return {"message": "Hello FastAPI !"}

@app.get("/echo/{text}")
async def handle_echo(text: str):
	return {"echo": text}

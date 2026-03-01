from typing import Annotated
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2AuthorizationCodeBearer

app = FastAPI()

# リクエストヘッダーからbearerトークンを抽出するオブジェクト
# tokenUrlは認証を行うエンドポイントを指定
oauth2 = OAuth2AuthorizationCodeBearer(tokenUrl="token")

@app.get("/items")
async def handle_items(token: Annotated[str, Depends(oauth2)]):
	return {"token": token}

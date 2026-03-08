"""
	03-08:	認証の実装
			itemエンドポイントの実装(items/idも)とデータベースの連携

"""
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from pydantic import BaseModel

app = FastAPI()

class Token(BaseModel):
	access_token: str
	token_type: str

@app.post("/token")
async def handle_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
	"""
	1. authenticate_userで、ユーザーの存在・ハッシュの一致を確認
		- ユーザーデータを取得
		- 存在しないなら401
	2. create_tokenでJWTトークンを作成
		- timedeltaで有効期限を設定
	3. Tokenインスタンスをレスポンス

	"""

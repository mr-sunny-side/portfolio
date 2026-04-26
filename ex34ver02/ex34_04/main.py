"""
	### 04-24: テストから

	### 環境構築
	 - 依存関係ファイルの作成(pip freeze > requirements.txt)	-
	 - 新規DBの作成												-
	 - alembicのインストール									-
	 - .envファイルの作成										-

	### アプリの構築
	 - token				 -
	 - users/register		 -  認証無しで追加可能、重複が発生
	 - users=get(認証なし)	 -
	 - users=delete			 -
	 - items=get(認証なし)	 -
	 - items=post			 -
	 - items=delete			 -
	 - コードのレビュー		 -


"""
from fastapi import FastAPI

app = FastAPI()

# ユーザーの追加(重複排除)
@app.post("/users/register")
async def handle_add_users():
	pass

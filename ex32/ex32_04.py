"""
	03-04: 4aの復習から

"""

from fastapi import FastAPI

app = FastAPI()

def authenticate_user():
	"""
	# パスとユーザーが正しい確認する関数

	1. ユーザーがDBに存在するか確認
		- 存在しないなら疑似確認を走らせる
	2. UserInDBにユーザー情報を変換
	3. ハッシュを確認
	4. UserInDBインスタンスをreturn

	"""

	pass

def create_token():
	"""
	# JWTトークンを作成する関数

	1. 作業用にusername(sub dict)をコピー
	2. 有効期限を作成
	3. トークンを反映し、作成

	"""
	pass


async def get_cur_user():
	"""
	# JWTトークンをデコードして認証を確認する関数

	1. トークンのデコード
	2. デコードしたトークンからusernameを取得
	3. TokenDataインスタンスとしてユーザー名を取得
	4. dbに存在するか確認し、UserInDBインスタンスに変換
	5. インスタンスをreturn

	"""

	pass

@app.post("/token")
async def handle_token():
	"""
	1. authenticate_userで、ユーザーの存在・ハッシュの一致を確認
		- 存在しないなら401
	2. create_access_tokenでJWTトークンを作成
		- timedeltaで有効期限を設定
	3. Tokenインスタンスをレスポンス

	"""
	pass

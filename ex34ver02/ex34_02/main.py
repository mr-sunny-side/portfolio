"""
	04-08: プロジェクトdirの環境構築から
	- 依存関係ファイルの作成(pip freeze > requirements.txt)
	- 新規DBの作成(postgresql)
	- alembicのインストール(コンテナの中でやったほうがいい？)
	- .envファイルの作成

	03-22:	アプリの構築
	 - token											 -
	 - user/register, users/me=delete, users/me/items	 -
	 - items=post, items=delete							 -
	 - dockerイメージの作成								 -
	 - engineの記述(db:5433へ接続)						 -
	 - マイグレーションの作成(コンテナ内で実行)			 -


"""

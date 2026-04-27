import os
import pytest
from sqlmodel import create_engine, Session, SQLModel
from fastapi.testclient import TestClient
import models

"""
	load_dotenv()は、環境変数が空の場合にのみ上書きする。
	なのでこのファイルで予めダミー環境変数を設定しておくことで
	テスト用の環境を用意する。
"""
# テスト環境用に環境変数をダミーに設定
os.environ["DATABASE_URL"] = "sqlite://"	# データベースのURLの形式である必要がある
os.environ["SECRET_KEY"] = "dummy"
os.environ["ALGORITHM"] = "HS256"

# 環境変数を設定した上でmainを呼び出す
from main import app, get_session

# テスト用のエンジンの作成(メモリで動作し、終了時に消滅)
SQLITE_URL = "sqlite://"
# 複数スレッドからの接続を許可
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

# テストで使うセッション関数を作成
def override_get_session():
	with Session(engine) as session:
		yield session

# pytestがテストコードを動かす際に使う関数
@pytest.fixture
def client():
	SQLModel.metadata.create_all(engine)	# テーブルの作成
	app.dependency_overrides[get_session] = override_get_session	# セッションの取得をsqliteに指定
	yield TestClient(app)	# HTTPリクエストを送れるオブジェクト
	SQLModel.metadata.drop_all(engine)	# テーブルを削除
	app.dependency_overrides.clear()	# オーバーライドの設定をリセット

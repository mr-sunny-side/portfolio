import os
import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
import models
from fastapi.testclient import TestClient

# 環境変数をテスト用に予め指定
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "dummy"
os.environ["ALGORITHM"] = "HS256"

# 環境変数を上書きした上で、mainを呼び出す
from main import app, get_session

# get_sessionを上書きするengineの作成
SQLITE_URL = "sqlite://"
engine = create_engine(
	SQLITE_URL,
	connect_args={"check_same_thread": False},	# 複数スレッドでの実行を許可
	poolclass=StaticPool	# これを付けないと、create_allで作ったテーブルに接続できない
)
# インメモリでは接続が切れた時点でデータが消えるので、一つの接続を使いまわす

def override_get_session():
	with Session(engine) as session:
		yield session

# pytestが呼び出すテスト用client関数を作成
@pytest.fixture
def client():	# 名前はclientで固定
	SQLModel.metadata.create_all(engine)	# テーブルを作成
	app.dependency_overrides[get_session] = override_get_session	# get_sessionをインメモリに書き換え
	yield TestClient(app)					# 叩くアプリを指定し、testclientを作成
	SQLModel.metadata.drop_all(engine)		# 終了時にテーブルを削除
	app.dependency_overrides.clear()		# get_sessionの上書きを解除

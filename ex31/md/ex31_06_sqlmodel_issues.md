# ex31_06 SQLModel テスト — 問題点まとめ

対象ファイル: `ex31_06.py` / `test_ex31_06.py`

---

## 問題 1: `Field` を `pydantic` からインポートしていた【修正済み】

### 症状

```
PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated
(Extra keys: 'primary_key')
sqlalchemy.exc.ArgumentError: Mapper[ItemDB(itemdb)] could not assemble any primary key columns
```

### 原因

`primary_key=True` は **SQLModel の `Field`** にしかない引数。
`pydantic` の `Field` に渡すと未知のキーとして無視され、プライマリキーが設定されないままテーブルマッピングが失敗する。

```python
# NG
from pydantic import BaseModel, Field          # pydantic の Field には primary_key がない
from sqlmodel import SQLModel, create_engine, Session, select

class ItemDB(ItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)  # primary_key が無視される
```

```python
# OK
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, create_engine, Session, select  # sqlmodel の Field を使う

class ItemDB(ItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)  # 正しく認識される
```

### 教訓

SQLModel のモデルで `Field` を使うときは必ず `sqlmodel` からインポートする。
`sqlmodel.Field` は `pydantic.Field` を内包しているため、`min_length` や `ge` など Pydantic の引数もそのまま使える。

---

## 問題 2: テーブルが作成されていない【未修正】

### 症状

`ex31_06.db` ファイルは存在するが、中にテーブルが一つもない。
テストを実行すると `no such table: itemdb` 系のエラーになる。

### 原因

`SQLModel.metadata.create_all(engine)` が一度も呼ばれていない。
SQLModel はクラスを定義しただけではテーブルを作らない。明示的に `create_all` を呼ぶ必要がある。

```python
# ex31_06.py に追記が必要
engine = create_engine(db_url, connect_args={"check_same_thread": False})
SQLModel.metadata.create_all(engine)   # ← これがないとテーブルが存在しない
```

ただし、本番コード側に書くとアプリ起動のたびに実行される。
テストでは後述のフィクスチャ内で呼ぶ方が望ましい。

---

## 問題 3: テストが本番 DB ファイルに書き込む【未修正】

### 症状

テストを実行するたびに `ex31_06.db` にデータが蓄積する。
2 回目以降の実行では `id` が 1 から始まらず、以下のアサーションが失敗する。

```python
assert response.json() == {"id": 1, "name": "apple", "price": 300, "tax": 0}  # id が 4, 7, ... になる
```

### 原因

`ex31_06.py` で本番用 DB URL をハードコードしており、テストもそのまま使ってしまっている。

```python
db_url = "sqlite:///ex31_06.db"   # 本番と同じファイルを使ってしまう
engine = create_engine(db_url, ...)
```

### 解決策: テスト用インメモリ DB + Depends のオーバーライド

```python
# test_ex31_06.py
import pytest
from sqlmodel import SQLModel, create_engine, Session
from starlette.testclient import TestClient
import ex31_06
from ex31_06 import app, get_session

TEST_DB_URL = "sqlite://"   # インメモリ DB（テスト終了で消える）
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})

def override_get_session():
    with Session(test_engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(autouse=True)
def reset_db():
    SQLModel.metadata.create_all(test_engine)   # テスト前にテーブル作成
    yield
    SQLModel.metadata.drop_all(test_engine)     # テスト後にテーブル削除

client = TestClient(app)
```

| 方法 | テストが汚染されるか | 再実行で id がズレるか |
|------|---------------------|----------------------|
| 本番 DB ファイルをそのまま使う | する | ズレる |
| インメモリ DB + fixture でリセット | しない | ズレない（毎回 1 から） |

---

## 問題 4: テスト間に暗黙の依存関係がある【設計上の問題】

### 症状

`test_one_items` は `id=2` の banana が存在することを前提にしているが、
その banana を登録しているのは別の `test_all_items` 関数。

```python
def test_all_items():
    client.post("/items", json={"name": "apple",  "price": 300})
    client.post("/items", json={"name": "banana", "price": 150})   # id=2 をここで作っている
    client.post("/items", json={"name": "orange", "price": 500})
    ...

def test_one_items():
    response = client.get("/items/2")   # test_all_items が先に走らないと存在しない
    assert response.json() == {"id": 2, "name": "banana", ...}
```

pytest はデフォルトでファイル内の記述順に実行するため今は動くが、
テストを並列実行したり順番を変えると壊れる。

### 解決策

各テストは独立して動くように書く。`test_one_items` の中で自分でデータを登録する。

```python
def test_one_items():
    # このテスト自身でデータを用意する
    client.post("/items", json={"name": "apple",  "price": 300})
    client.post("/items", json={"name": "banana", "price": 150})

    response = client.get("/items/2")
    assert response.status_code == 200
    assert response.json() == {"id": 2, "name": "banana", "price": 150, "tax": 0}
```

---

## まとめ

| # | 問題 | 深刻度 | 状態 |
|---|------|--------|------|
| 1 | `Field` を `pydantic` からインポートしていた | エラー（起動不可） | 修正済み |
| 2 | `create_all` が呼ばれていない | エラー（テーブルなし） | 未修正 |
| 3 | 本番 DB ファイルをテストに使っている | データ汚染・id ズレ | 未修正 |
| 4 | テスト間に暗黙の依存がある | テスト順序依存で壊れる | 未修正 |

### SQLModel テスト の定石

```
1. テスト用エンジンは sqlite:// (インメモリ) を使う
2. Depends(get_session) を app.dependency_overrides でテスト用に差し替える
3. autouse=True のフィクスチャで create_all / drop_all する
4. 各テストは独立して動くように書く（他のテストのデータに頼らない）
```

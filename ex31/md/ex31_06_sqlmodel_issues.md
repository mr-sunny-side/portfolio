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

## 問題 3 の詳細解説: テストが本番 DB ファイルに書き込む

### まず「DB ファイル」と「インメモリ DB」の違いから

`ex31_06.py` には以下の行がある。

```python
db_url = "sqlite:///ex31_06.db"
```

`sqlite:///ex31_06.db` は「`ex31_06.db` という**ファイル**に保存する」という意味。
ファイルなので、プログラムを終了しても中のデータは消えない。

```
1回目のテスト実行:  ex31_06.db に apple(id=1), banana(id=2), orange(id=3) が保存される
2回目のテスト実行:  同じファイルに追加されるので apple(id=4), banana(id=5), orange(id=6) になる
3回目のテスト実行:  apple(id=7), banana(id=8), orange(id=9) ...
```

テストは `id=1` を期待しているので、2 回目以降は必ず失敗する。

```
# インメモリ DB の URL
sqlite://        ← ファイルを作らない。プログラムが終わったらデータが消える
sqlite:///foo.db ← foo.db というファイルに保存する。データが残り続ける
```

インメモリ DB はメモリ上にだけ存在するため、テストが終わると自動的に消える。
毎回テストを実行するたびに「新品の空のDB」から始められる。

---

### なぜテストから本番 DB が使われてしまうのか

テストファイルは `import ex31_06` している。
`ex31_06.py` が import されると、その中のコードが実行される。

```python
# ex31_06.py の中
db_url = "sqlite:///ex31_06.db"          # ← import 時にここが実行される
engine = create_engine(db_url, ...)      # ← ここも実行される
```

つまり **テストが import しただけで、本番 DB への接続が確立してしまう**。

エンドポイント（`handle_add_items` など）の中で `get_session` が呼ばれると、
この本番 engine を使ってセッションが作られ、本番 DB に書き込む。

```
テスト → TestClient → FastAPI → handle_add_items → get_session → engine(本番) → ex31_06.db
```

---

### `Depends` と `get_session` の仕組み

`ex31_06.py` のエンドポイントは以下のように書かれている。

```python
@app.post("/items", ...)
async def handle_add_items(
    item: ItemGet,
    session: Annotated[Session, Depends(get_session)]   # ← ここ
):
```

`Depends(get_session)` は「この引数 `session` の値は `get_session` 関数を呼んで用意してください」という FastAPI への指示。
これを**依存性注入（Dependency Injection）** と呼ぶ。

```
リクエストが来る
  ↓
FastAPI が Depends(get_session) を見つける
  ↓
get_session() を実行してセッションを作る
  ↓
できたセッションを session 引数として渡す
  ↓
handle_add_items の本体が実行される
```

ポイントは「**どのエンジンを使うか**は `get_session` の中で決まっている」こと。

```python
async def get_session():
    with Session(engine) as session:   # ← engine = 本番 DB のエンジン
        yield session
```

---

### `dependency_overrides` で差し替える

FastAPI には `app.dependency_overrides` という辞書がある。
「この Depends を、テスト中は代わりにこっちの関数で処理してください」と登録できる。

```python
# test_ex31_06.py

# 1. テスト用のエンジンを作る（インメモリ DB）
test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})

# 2. テスト用のセッション生成関数を作る
def override_get_session():
    with Session(test_engine) as session:   # ← test_engine（インメモリ）を使う
        yield session

# 3. 本番の get_session をテスト用に差し替える
app.dependency_overrides[get_session] = override_get_session
```

これを設定すると、エンドポイントが `Depends(get_session)` を呼ぼうとしたとき、
FastAPI は代わりに `override_get_session` を実行する。

```
テスト中のリクエストの流れ:
  handle_add_items
    ↓ Depends(get_session) が呼ばれる
    ↓ dependency_overrides に get_session の上書きがある!
    ↓ override_get_session() が実行される
    ↓ test_engine（インメモリ DB）を使ったセッションが渡される
    ↓ インメモリ DB に書き込まれる（本番 DB は汚染されない）
```

---

### `@pytest.fixture` と `autouse=True` と `yield`

```python
@pytest.fixture(autouse=True)
def reset_db():
    SQLModel.metadata.create_all(test_engine)   # テスト前に実行
    yield                                        # ← ここでテスト本体が走る
    SQLModel.metadata.drop_all(test_engine)     # テスト後に実行
```

`@pytest.fixture` は「テストの前後に実行したい処理」を定義する仕組み。
`autouse=True` は「すべてのテスト関数に自動で適用する」という意味。

`yield` を境に「前処理」と「後処理」が分かれる。

```
テスト関数が実行されるたびに:

  [前処理] create_all → テーブルを作る（空のDB）
      ↓
  [テスト本体] test_all_items(), test_one_items() など
      ↓
  [後処理] drop_all → テーブルを消す
```

`drop_all` でテーブルを消してから `create_all` で作り直すので、
毎回テストが「空のDB」から始まる。

```
test_all_items 実行時:
  create_all → [空] → POST apple(id=1), banana(id=2), orange(id=3) → drop_all → [消える]

test_one_items 実行時:
  create_all → [空] → POST apple(id=1), banana(id=2) → GET /items/2 → drop_all → [消える]
```

---

## 問題 4 の詳細解説: テスト間に暗黙の依存関係がある

### 「テストの独立性」とは何か

良いテストの条件の一つに「**どの順番で実行しても結果が変わらない**」がある。

現在の `test_one_items` はこうなっている。

```python
def test_one_items():
    response = client.get("/items/2")
    assert response.json() == {"id": 2, "name": "banana", "price": 150, "tax": 0}
```

`/items/2` が存在するためには、事前に banana が登録されている必要がある。
banana を登録しているのは `test_all_items`。

```python
def test_all_items():
    client.post("/items", json={"name": "apple",  "price": 300})  # id=1
    client.post("/items", json={"name": "banana", "price": 150})  # id=2 ← banana はここで作られる
    client.post("/items", json={"name": "orange", "price": 500})  # id=3
    ...
```

つまり `test_one_items` は `test_all_items` が先に実行されないと動かない。

---

### なぜ今は動いているのか

pytest はデフォルトで「ファイルに書かれた順番」でテストを実行する。

```
test_index        (1番目)
test_echo         (2番目)
test_all_items    (3番目) ← banana を登録する
test_one_items    (4番目) ← banana を使う  ← 今は順番が正しいので動く
test_error_echo   (5番目)
test_error_add    (6番目)
test_404_items    (7番目)
```

たまたま `test_all_items` が先に来ているので動いているだけ。

---

### 問題 3（フィクスチャでリセット）と組み合わさると確実に壊れる

問題 3 の解決策（フィクスチャで毎回 DB をリセット）を導入すると:

```
test_all_items: [空のDB] → apple, banana, orange を登録 → [リセット・消える]
test_one_items: [空のDB] → /items/2 を GET → 空なので 404 → テスト失敗
```

`test_all_items` が登録したデータはリセットで消えるため、
`test_one_items` が実行されるときには banana が存在しない。

問題 3 と問題 4 は**セットで直す必要がある**。

---

### 解決策: 各テストが自分でデータを用意する

```python
def test_one_items():
    # このテスト自身で必要なデータを登録する
    client.post("/items", json={"name": "apple",  "price": 300})  # id=1
    client.post("/items", json={"name": "banana", "price": 150})  # id=2

    response = client.get("/items/2")
    assert response.status_code == 200
    assert response.json() == {"id": 2, "name": "banana", "price": 150, "tax": 0}
```

こうすると:

```
test_one_items: [空のDB] → apple(id=1), banana(id=2) を自分で登録 → /items/2 を GET → 成功
```

`test_all_items` が先に実行されているかどうかに関わらず、このテスト単体で完結する。

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

# FastAPI テストコード 学習ガイド

対象: `02_ex31.py` のエンドポイントをテストする

---

## 1. なぜ TestClient を使うのか

FastAPI には `starlette.testclient.TestClient` が付属している。
これを使うと **サーバーを起動せず** にリクエストを送れる。

```
curl でテスト          →  uvicorn を起動 → curl → 結果確認 (毎回手動)
TestClient でテスト    →  Python 内で完結 → pytest が自動実行
```

---

## 2. セットアップ

```bash
cd ex31
source venv/bin/activate
pip install pytest          # テストランナー（未インストールの場合）
```

---

## 3. 基本構造

```python
from starlette.testclient import TestClient
from .your_app import app           # FastAPI の app オブジェクトを import

client = TestClient(app)            # ← サーバー起動なし

def test_something():
    response = client.get("/")      # ← HTTP リクエストを送る
    assert response.status_code == 200
    assert response.json() == {"message": "Hello FastAPI !"}
```

### TestClient のメソッド一覧

| メソッド                              | 対応する HTTP メソッド |
|---------------------------------------|------------------------|
| `client.get("/path")`                 | GET                    |
| `client.post("/path", json={...})`    | POST (JSON ボディ)     |
| `client.put("/path", json={...})`     | PUT                    |
| `client.delete("/path")`              | DELETE                 |

### response オブジェクトの属性

```python
response.status_code    # 200, 404, 422 など
response.json()         # レスポンスボディを辞書として取得
response.text           # レスポンスボディを文字列として取得
```

---

## 4. ファイル名が数字始まりのとき (例: `02_ex31.py`)

Python は `import 02_ex31` と書けない（数字始まりは無効な識別子）。
そのため `importlib` で読み込む。

```python
import importlib.util

spec = importlib.util.spec_from_file_location(
    "app_module",                               # Python 内での呼び名（任意）
    "/絶対パス/ex31/02_ex31.py"                 # ファイルの場所
)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)             # モジュールを実行して読み込む

app = app_module.app                            # app オブジェクトを取り出す
```

> **補足**: ファイルを `ex31_02.py` のように数字以外で始めると
> `from ex31_02 import app` で普通に import できる。

---

## 5. pytest フィクスチャ

### フィクスチャとは

テストの「前処理・後処理」を定義する仕組み。
`@pytest.fixture` デコレータを付けた関数がフィクスチャになる。

```python
import pytest

@pytest.fixture
def client():
    return TestClient(app)      # テストのたびに client を生成して渡す
```

テスト関数の **引数名** をフィクスチャ名と同じにすると、自動で注入される。

```python
def test_index(client):         # ← client フィクスチャが自動で渡される
    response = client.get("/")
    assert response.status_code == 200
```

### yield を使ったセットアップ / ティアダウン

```python
@pytest.fixture
def client():
    # --- セットアップ (テスト前) ---
    c = TestClient(app)
    yield c                     # ← ここでテスト関数に値を渡す
    # --- ティアダウン (テスト後) ---
    # 後片付けの処理をここに書く
```

### autouse=True : 全テストに自動適用

`02_ex31.py` は `items` リストをグローバル変数として持っている。
テストごとにリセットしないと、前のテストの結果が残ってしまう。

```python
@pytest.fixture(autouse=True)   # ← 全テストに自動で適用
def reset_state():
    app_module.items.clear()
    app_module.item_id = 0
    yield
    app_module.items.clear()    # テスト後もリセット
    app_module.item_id = 0
```

`autouse=True` があると、テスト関数の引数に書かなくても自動で実行される。

---

## 6. テストの書き方

### GET リクエスト

```python
def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello FastAPI !"}
```

### パスパラメータ付き GET

```python
def test_echo(client):
    response = client.get("/echo/hello")
    assert response.json() == {"echo": "hello"}
```

### POST リクエスト (JSON ボディ)

```python
def test_add_item(client):
    response = client.post("/items", json={
        "name": "Apple",
        "price": 100,
        "tax": 0.1
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Apple"
    assert data["id"] == 0          # 最初の item は id=0
```

### クエリパラメータ付き GET

```python
def test_items_with_params(client):
    response = client.get("/items", params={"skip": 0, "limit": 5})
    assert response.status_code == 200
```

### バリデーションエラーのテスト

FastAPI は必須フィールドが欠けていると **422** を返す。

```python
def test_missing_price(client):
    response = client.post("/items", json={"name": "Apple"})  # price がない
    assert response.status_code == 422
```

### 複数テストの連携 (POST してから GET)

```python
def test_get_one_item(client):
    # まず POST して item を作る
    post_res = client.post("/items", json={"name": "Orange", "price": 80})
    item_id = post_res.json()["id"]

    # 作った item を GET で取得
    get_res = client.get(f"/items/{item_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Orange"
```

---

## 7. テストをクラスでまとめる

エンドポイントごとにクラスにまとめると読みやすくなる。

```python
class TestAddItems:
    def test_with_tax(self, client):
        ...

    def test_without_tax(self, client):
        ...

class TestAllItems:
    def test_empty(self, client):
        ...
```

> クラス内のメソッドは `self` が必要な点に注意。

---

## 8. 実行コマンド

```bash
# 全テストを実行
pytest test_02_ex31.py

# 詳細表示 (テスト名と結果を表示)
pytest test_02_ex31.py -v

# 特定のクラスだけ実行
pytest test_02_ex31.py::TestAddItems -v

# 特定のテストだけ実行
pytest test_02_ex31.py::TestAddItems::test_with_tax -v

# 失敗したテストで即停止
pytest test_02_ex31.py -x
```

---

## 9. ステータスコード早見表

| コード | 意味                                      | FastAPI での発生場面          |
|--------|-------------------------------------------|-------------------------------|
| 200    | OK                                        | 正常なレスポンス              |
| 404    | Not Found                                 | `HTTPException(404)` を raise |
| 422    | Unprocessable Entity (バリデーションエラー) | Pydantic の型チェック失敗     |
| 500    | Internal Server Error                     | 未キャッチの例外              |

> `02_ex31.py` は item が見つからない場合も 200 を返している。
> 本来は `HTTPException(status_code=404)` を使うのが REST の慣習。

---

## 10. 既存コードのバグ例

`02_ex31.py` の `/items/{id}` には型アノテーションが必要。

```python
# NG: id が str のまま → i['id'] (int) と一致しない
async def one_items(id):
    item = next((i for i in items if i['id'] == id), None)

# OK: FastAPI が str → int に変換してくれる
async def one_items(id: int):
    item = next((i for i in items if i['id'] == id), None)
```

テストを書くことでこういったバグを早期発見できる。

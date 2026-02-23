# FastAPI テストコード 学習ガイド

対象: `02_ex31.py` のエンドポイントをテストする

---

## 0. そもそも pytest とは何か

`pytest` は「テストを自動で実行してくれるツール」。

手動でやっていたこと：
```
1. uvicorn を起動する
2. curl でリクエストを打つ
3. 返ってきた JSON を目で確認する
4. 正しければ OK、違えば修正する
```

pytest でやること：
```
1. pytest コマンドを 1 回打つ
2. 全部自動で確認してくれる
3. 通過 → .(ドット)、失敗 → F(エフ) で一覧表示
```

---

## 1. テスト関数の最低限のルール

pytest は以下のルールに従って「テスト関数」を自動で見つけて実行する。

```
ファイル名  → test_ で始まるか、_test で終わる  例: test_02_ex31.py
関数名      → test_ で始まる                    例: def test_index():
```

中身は `assert`（アサート）で確認する。

```python
# assert の使い方
assert 1 + 1 == 2       # 通過（True なので OK）
assert 1 + 1 == 3       # 失敗（False なので FAILED と表示される）
```

`assert A == B` は「A と B が等しいことを確認せよ」という命令。
等しくなければテスト失敗として報告される。

---

## 2. セットアップ

```bash
cd ex31
source venv/bin/activate
pip install pytest
```

---

## 3. TestClient とは

FastAPI には `TestClient` という道具が付属している。
これは「curl の代わりに Python の中からリクエストを送る」ためのもの。

```
curl でテスト       → サーバーを起動してから curl を打つ（毎回手動）
TestClient でテスト → サーバー起動不要、Python の中で完結
```

使い方：

```python
from starlette.testclient import TestClient
from your_app import app       # FastAPI の app を読み込む

client = TestClient(app)       # これが curl の代わり

response = client.get("/")     # GET / を送る
print(response.status_code)    # 200
print(response.json())         # {"message": "Hello FastAPI !"}
```

`client.get()` が curl の `curl http://localhost:8000/` に相当する。

### TestClient のメソッド

| TestClient                                  | curl 相当                                                    |
|---------------------------------------------|--------------------------------------------------------------|
| `client.get("/items")`                      | `curl http://localhost:8000/items`                           |
| `client.post("/items", json={"name":"A"})`  | `curl -X POST -H "Content-Type: application/json" -d '{"name":"A"}' .../items` |

---

## 4. ファイル名が数字始まり問題

Python は数字で始まるファイル名を `import` できない。

```python
import 02_ex31   # エラー！ (SyntaxError)
```

回避策として `importlib` を使う。難しく見えるが「数字始まりのファイルを読み込むおまじない」と覚えておけばよい。

```python
import importlib.util

# ファイルを指定して読み込む
spec = importlib.util.spec_from_file_location(
    "app_module",                                    # Python 内での呼び名（何でもよい）
    "/home/kimetenai/portfolio/ex31/02_ex31.py"      # ファイルの絶対パス
)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

# 読み込んだモジュールから app を取り出す
app = app_module.app
```

> **補足**: `02_ex31.py` を `ex31_02.py` に名前変更すれば `from ex31_02 import app` で普通に書ける。

---

## 5. 最初のテストファイルを書く

ここまでの知識でテストを書ける。

```python
# test_02_ex31.py

import importlib.util
from starlette.testclient import TestClient

# --- 02_ex31.py を読み込む ---
spec = importlib.util.spec_from_file_location(
    "app_module",
    "/home/kimetenai/portfolio/ex31/02_ex31.py"
)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = app_module.app

# --- TestClient を作る ---
client = TestClient(app)

# --- テスト関数 ---
def test_index():
    response = client.get("/")             # GET / を送る
    assert response.status_code == 200     # ステータスコードが 200 か確認
    assert response.json() == {"message": "Hello FastAPI !"}   # 中身を確認
```

実行：

```bash
pytest test_02_ex31.py -v
```

出力例（成功）：

```
PASSED test_02_ex31.py::test_index
```

出力例（失敗）：

```
FAILED test_02_ex31.py::test_index
AssertionError: assert {"message": "Hello"} == {"message": "Hello FastAPI !"}
```

---

## 6. assert の書き方パターン

```python
# 等しい
assert response.status_code == 200

# 等しくない
assert response.status_code != 500

# 辞書の中身を確認
data = response.json()
assert data["name"] == "Apple"
assert data["id"] == 0

# リストの長さを確認
assert len(data) == 2

# None かどうか
assert data["tax"] is None

# 辞書全体を一致確認
assert response.json() == {"message": "Item not found"}
```

---

## 7. エンドポイント別のテスト例

### GET /echo/{text}  ← パスパラメータ

```python
def test_echo():
    response = client.get("/echo/hello")   # /echo/hello に GET
    assert response.status_code == 200
    assert response.json() == {"echo": "hello"}
```

### POST /items  ← リクエストボディ

```python
def test_add_item():
    response = client.post(
        "/items",
        json={"name": "Apple", "price": 100, "tax": 0.1}   # JSON ボディ
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Apple"
    assert data["price"] == 100
    assert data["id"] == 0          # 最初の item は id=0
```

### GET /items  ← クエリパラメータ

```python
def test_all_items():
    response = client.get("/items", params={"skip": 0, "limit": 10})
    assert response.status_code == 200
    assert response.json() == []    # まだ何も登録していなければ空リスト
```

### POST してから GET  ← テストを連携させる

```python
def test_get_one_item():
    # 先に POST して item を作る
    post_res = client.post("/items", json={"name": "Orange", "price": 80})
    item_id = post_res.json()["id"]        # 返ってきた id を取り出す

    # その id で GET する
    get_res = client.get(f"/items/{item_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Orange"
```

### バリデーションエラー (422)

FastAPI は必須フィールドが欠けていると **422** を返す。

```python
def test_missing_price():
    response = client.post("/items", json={"name": "Apple"})   # price がない
    assert response.status_code == 422
```

---

## 8. フィクスチャ (fixture)

### 問題：テスト間でデータが引き継がれてしまう

`02_ex31.py` の `items` リストはグローバル変数。
テスト A で POST した item が、テスト B にも残ってしまう。

```
テスト A: POST Apple → items = [Apple]
テスト B: GET /items → items = [Apple] ← A の結果が残っている！
          assert len(items) == 0  → 失敗
```

### 解決策：フィクスチャでリセットする

`@pytest.fixture` は「テストの前後に実行したい処理」を定義するデコレータ。

```python
import pytest

@pytest.fixture(autouse=True)    # autouse=True = 全テストに自動で適用
def reset_state():
    # --- テスト前 ---
    app_module.items.clear()     # items を空にする
    app_module.item_id = 0       # id カウンターをリセット
    yield                        # ← ここでテスト本体が実行される
    # --- テスト後 ---
    app_module.items.clear()     # テスト後もリセット
    app_module.item_id = 0
```

`autouse=True` を付けると、全テスト関数に自動で適用される。
テスト関数側に何も書かなくてよい。

```
テスト A: [リセット] → POST Apple → [リセット]
テスト B: [リセット] → GET /items → items = []  → assert len == 0 → 通過
```

### フィクスチャを値として受け取る

`autouse` なしで、テスト関数が値を受け取るパターン。

```python
@pytest.fixture
def client():
    return TestClient(app)
```

テスト関数の引数名をフィクスチャ名と同じにすると、自動で注入される。

```python
def test_index(client):          # ← 引数名 client = フィクスチャ名 client
    response = client.get("/")
    assert response.status_code == 200
```

---

## 9. 実行コマンド

```bash
# 全テストを実行
pytest test_02_ex31.py

# 詳細表示（テスト名と PASSED / FAILED を表示）
pytest test_02_ex31.py -v

# 特定のテスト関数だけ実行
pytest test_02_ex31.py::test_index -v

# 失敗したら即停止（デバッグ時に便利）
pytest test_02_ex31.py -x
```

---

## 10. ステータスコード早見表

| コード | 意味                        | いつ来るか                           |
|--------|-----------------------------|--------------------------------------|
| 200    | OK（成功）                  | 正常なレスポンス                     |
| 422    | バリデーションエラー        | 必須フィールドがない、型が違うなど   |
| 404    | Not Found                   | `HTTPException(404)` を使ったとき    |
| 500    | サーバー内部エラー          | 未処理の例外が発生したとき           |

> `02_ex31.py` は item が見つからない場合も 200 を返しているが、
> 本来は 404 を返すのが REST の慣習。

---

## 11. ここまでのまとめ

```
pytest        → テストを自動実行するツール
test_ 関数    → pytest が探して実行する関数
assert        → 「このはずだ」を確認する命令
TestClient    → サーバー不要で HTTP リクエストを送る道具
@pytest.fixture → テストの前後処理を定義するデコレータ
autouse=True  → 全テストに自動適用
yield         → テスト前 / テスト後を分ける区切り
```

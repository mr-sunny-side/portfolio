# PUT・DELETE メソッドの実装ガイド

## 概要

現在のコードには以下のエンドポイントがあります。

| メソッド | パス          | 説明                   |
|----------|---------------|------------------------|
| GET      | `/`           | インデックス           |
| GET      | `/echo/{text}`| エコー                 |
| POST     | `/items`      | アイテム追加           |
| GET      | `/items`      | 全アイテム取得         |
| GET      | `/items/{id}` | 1件取得                |

これに以下を追加します。

| メソッド | パス          | 説明                   |
|----------|---------------|------------------------|
| PUT      | `/items/{id}` | アイテム更新           |
| DELETE   | `/items/{id}` | アイテム削除           |

---

## PUT メソッド（更新）

### 役割
既存のアイテムを **上書き更新** する。

### 実装コード

```python
@app.put("/items/{id}", response_model=ItemResponse)
async def handle_update_item(
    id: Annotated[int, Path(ge=1)],
    item_data: ItemAdd,
    session: Annotated[Session, Depends(get_session)]
):
    # 1. DBから対象アイテムを取得
    item = session.get(ItemDB, id)

    # 2. 存在しなければ404エラー
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # 3. リクエストのデータをdictに変換して既存アイテムに反映
    update_data = item_data.model_dump()
    item.sqlmodel_update(update_data)

    # 4. コミットして最新状態に更新
    session.add(item)
    session.commit()
    session.refresh(item)

    return item
```

### 処理の流れ

```
リクエスト: PUT /items/3  body: { "name": "新商品", "price": 500, "tax": 0.1 }
         │
         ▼
   session.get(ItemDB, 3)  ← IDでDBを検索
         │
    見つからない → 404 HTTPException
         │
    見つかった
         ▼
   item_data.model_dump()  ← { "name": "新商品", "price": 500, "tax": 0.1 }
         │
         ▼
   item.sqlmodel_update(update_data)  ← 既存アイテムのフィールドを上書き
         │
         ▼
   session.add(item) → session.commit() → session.refresh(item)
         │
         ▼
   レスポンス: { "id": 3, "name": "新商品", "price": 500, "tax": 0.1 }
```

### ポイント解説

#### `item_data.model_dump()`
Pydantic / SQLModel のモデルを Python の辞書（dict）に変換します。

```python
item_data.model_dump()
# → { "name": "新商品", "price": 500, "tax": 0.1 }
```

#### `item.sqlmodel_update(update_data)`
SQLModel が提供するメソッドで、辞書のキー・バリューを既存モデルのフィールドに一括反映します。

```python
# 内部的にはこれと同じ意味
item.name = update_data["name"]
item.price = update_data["price"]
item.tax = update_data["tax"]
```

---

## DELETE メソッド（削除）

### 役割
指定 ID のアイテムを **DB から削除** する。

### 実装コード

```python
@app.delete("/items/{id}", status_code=204)
async def handle_delete_item(
    id: Annotated[int, Path(ge=1)],
    session: Annotated[Session, Depends(get_session)]
):
    # 1. DBから対象アイテムを取得
    item = session.get(ItemDB, id)

    # 2. 存在しなければ404エラー
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # 3. 削除してコミット
    session.delete(item)
    session.commit()

    # 4. 204はレスポンスボディなし（return不要）
```

### 処理の流れ

```
リクエスト: DELETE /items/3
         │
         ▼
   session.get(ItemDB, 3)  ← IDでDBを検索
         │
    見つからない → 404 HTTPException
         │
    見つかった
         ▼
   session.delete(item)  ← セッション上で削除をマーク
         │
         ▼
   session.commit()  ← DBに削除を確定
         │
         ▼
   レスポンス: 204 No Content（ボディなし）
```

### ポイント解説

#### `status_code=204`
削除成功時は **204 No Content** を返すのが REST の慣例です。
204 はレスポンスボディを持たないため、`return` 文は不要です。

| ステータスコード | 意味                   | ボディ |
|-----------------|------------------------|--------|
| 200 OK          | 成功（データあり）     | あり   |
| 201 Created     | 作成成功               | あり   |
| 204 No Content  | 成功（データなし）     | なし   |
| 404 Not Found   | リソースが存在しない   | あり   |

#### `session.delete(item)` と `session.commit()`
- `session.delete(item)` はメモリ上のセッションに「削除予定」を登録するだけ
- `session.commit()` を呼ぶことで初めて DB に削除が反映される

---

## 完成後のコード全体

```python
"""
    02-27:  - 06の復習
            - PUT, DELETEの追加
"""
from typing import Annotated
from fastapi import FastAPI, Path, Query, Depends, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select

app = FastAPI()

db_url = "sqlite:///ex31_06a.db"
engine = create_engine(db_url, connect_args={"check_same_thread": False})

class ItemBase(SQLModel):
    name: str = Field(min_length=1)
    price: int = Field(ge=0)
    tax: float = Field(default=0, ge=0)

class ItemAdd(ItemBase):
    pass

class ItemDB(ItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class ItemResponse(ItemBase):
    id: int

SQLModel.metadata.create_all(engine)

async def get_session():
    with Session(engine) as session:
        yield session

@app.get("/")
async def handle_index():
    return {"message": "Hello FastAPI !"}

@app.get("/echo/{text}")
async def handle_echo(text: str):
    return {"echo": text}

@app.post("/items", response_model=ItemResponse, status_code=201)
async def handle_add_items(
    item: ItemAdd,
    session: Annotated[Session, Depends(get_session)]
):
    item = ItemDB.model_validate(item)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@app.get("/items", response_model=list[ItemResponse])
async def handle_all_items(
    session: Annotated[Session, Depends(get_session)]
):
    return session.exec(select(ItemDB)).all()

@app.get("/items/{id}", response_model=ItemResponse)
async def handle_one_items(
    id: Annotated[int, Path(ge=1)],
    session: Annotated[Session, Depends(get_session)]
):
    item = session.get(ItemDB, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# --- 追加: PUT ---
@app.put("/items/{id}", response_model=ItemResponse)
async def handle_update_item(
    id: Annotated[int, Path(ge=1)],
    item_data: ItemAdd,
    session: Annotated[Session, Depends(get_session)]
):
    item = session.get(ItemDB, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    update_data = item_data.model_dump()
    item.sqlmodel_update(update_data)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

# --- 追加: DELETE ---
@app.delete("/items/{id}", status_code=204)
async def handle_delete_item(
    id: Annotated[int, Path(ge=1)],
    session: Annotated[Session, Depends(get_session)]
):
    item = session.get(ItemDB, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
```

---

## Q: `model_validate` で更新してはダメか？

### 結論：エラーになる

POST では `model_validate` を使っています。PUT でも同じように書けそうに見えますが、**セッションの衝突エラー**が発生します。

### なぜ POST は OK で PUT はダメか

| 操作 | `session.get()` を呼ぶか | セッション状態 |
|------|--------------------------|----------------|
| POST | 呼ばない                 | 空（追跡中のオブジェクトなし） |
| PUT  | 呼ぶ（存在確認のため）   | id=3 を**追跡中** |

PUT では `session.get()` の時点でセッションが対象オブジェクトを追跡し始めます。
その後 `model_validate` で **新しいオブジェクト** を作って同じ id を付けると衝突します。

```python
item = session.get(ItemDB, 3)        # セッションが id=3 を追跡開始

new_item = ItemDB.model_validate(item_data)
new_item.id = 3

session.add(new_item)                # ❌ id=3 は既に追跡中 → 衝突
# InvalidRequestError: Can't attach instance...
#   another instance with key (ItemDB, (3,)) is already present in this session
```

### `sqlmodel_update` が正解な理由

`sqlmodel_update` は新しいオブジェクトを作らず、**追跡中のオブジェクトのフィールドを直接書き換える**ため衝突しません。

```
session.get()        →  id=3 のオブジェクトを「追跡中」にする
                                ↓
item.sqlmodel_update()  →  追跡中オブジェクトのフィールドを直接書き換える
                           （新しいオブジェクトは作らない）
                                ↓
session.commit()     →  変更を検知して UPDATE 文を発行
```

### 強引に `model_validate` を使う方法（参考・非推奨）

`session.merge()` を使えば衝突は回避できますが、コードが複雑になります。

```python
item = session.get(ItemDB, id)
if not item:
    raise HTTPException(status_code=404, detail="Item not found")

new_item = ItemDB.model_validate(item_data)
new_item.id = id
merged = session.merge(new_item)  # ← 既存セッションと統合してくれる
session.commit()
session.refresh(merged)
return merged
```

`sqlmodel_update` の方がシンプルで SQLModel の想定パターンのため、こちらを使うのが正解。

---

## GET との比較（パターンの共通点）

PUT と DELETE は GET `/items/{id}` と同じ **「IDで1件取得 → 処理 → コミット」** のパターンです。

```
GET    /items/{id}  → 取得して return
PUT    /items/{id}  → 取得して更新して return
DELETE /items/{id}  → 取得して削除して return なし
```

この共通パターンを覚えると、他の CRUD 操作も自然に書けるようになります。

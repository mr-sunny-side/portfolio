# ex33_07 - SQLModel リレーションシップとAlembicの解説

## 今回の目標

`UserEx07` テーブルと `ItemEx07` テーブルを外部キーで紐付け（1対多のリレーションシップ）し、Alembic でマイグレーションを管理する。

---

## models.py のバグと修正

### バグ1: `UserEx07` に `table=True` がない

```python
# NG
class UserEx07(SQLModel):
    ...

# OK
class UserEx07(SQLModel, table=True):
    ...
```

`table=True` がないと SQLModel はそのクラスをDBテーブルとして認識しない。
Alembic の `autogenerate` も `table=True` のクラスのみを検出するため、何も生成されなかった原因はこれ。

---

### バグ2: Line 40 の構文エラー（`=` が2つある）

```python
# NG - = が2つある（代入と型アノテーションの混在）
items = list[ItemResponse] | None = None

# OK - : で型アノテーション、Relationship で定義
items: list["ItemEx07"] = Relationship(back_populates="owner")
```

Python のフィールド定義は `フィールド名: 型 = デフォルト値` の形式。
また `items` の型は `ItemResponse`（Pydanticモデル）ではなく、DBテーブルクラスの `ItemEx07` を使う。

---

### バグ3: `foreign_key` の指定方法が間違い

```python
# NG - Python の属性参照はNG
user_id: int | None = Field(default=None, foreign_key=UserEx07.id)

# OK - 文字列で "テーブル名.カラム名" を指定
user_id: int | None = Field(default=None, foreign_key="userex07.id")
```

SQLModel の `foreign_key` は**文字列**で指定する。テーブル名はクラス名を小文字にしたもの（`UserEx07` → `userex07`）。

---

### バグ4: `back_populates` の名前が不一致

```python
# NG - UserEx07 に "Items" というフィールドは存在しない
owner: "UserEx07" | None = Relationship(back_populates="Items")

# OK - UserEx07 側のフィールド名 "items" と一致させる
owner: "UserEx07" | None = Relationship(back_populates="items")
```

`back_populates` は双方向リレーションシップの設定。お互いのクラスで **同じ名前のペア** を指定する必要がある。

---

## 修正後の models.py（該当部分）

```python
class UserEx07(SQLModel, table=True):          # table=True を追加
    id: int | None = Field(default=None, primary_key=True)
    username: str
    password: str
    email: str | None = None
    disabled: bool | None = False
    items: list["ItemEx07"] = Relationship(back_populates="owner")  # ← Relationship で定義

class ItemEx07(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    price: int
    user_id: int | None = Field(default=None, foreign_key="userex07.id")  # ← 文字列で指定
    owner: "UserEx07" | None = Relationship(back_populates="items")       # ← "items" に合わせる
```

---

## 1対多リレーションシップの構造

```
UserEx07 (1)  ────────── (多) ItemEx07
    id  ←─────────────── user_id (外部キー)
    items (Relationship) owner (Relationship)
```

- `UserEx07.items` → そのユーザーが持つ全 Item のリスト
- `ItemEx07.owner` → その Item を所有する User

---

## Alembic で何も生成されなかった理由まとめ

| 原因 | 説明 |
|------|------|
| `table=True` がない | Alembic の autogenerate はテーブルクラスを検出できない |
| 構文エラー | クラス定義が壊れていると import 自体が失敗する可能性がある |
| `foreign_key` の型エラー | `UserEx07.id` は Python の属性参照で、評価時にエラーになる |

Alembic の `autogenerate` が `pass` のみのマイグレーションを生成した場合、まず **モデルが正しく import されているか**・**`table=True` があるか** を確認する。

---

## Alembic env.py でのインポート確認

```python
# env.py に必ず対象モデルのインポートを追加する
from models import UserEx07, ItemEx07
from sqlmodel import SQLModel
target_metadata = SQLModel.metadata
```

インポートがなければ Alembic はテーブルの存在を知ることができず、`pass` のみのマイグレーションが生成される。

---

## main.py の /items エンドポイント

```python
@app.post("/items")
async def handle_add_items(
    item: Item,
    cur_user: Annotated[UserResponse, Depends(get_cur_user)],  # 認証済みユーザーを取得
    session: Annotated[Session, Depends(get_session)]
) -> UserResponse:
    db_item = ItemEx07.model_validate(item)
    db_item.user_id = cur_user.id   # ← ログイン中のユーザーIDを紐付け
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return cur_user
```

JWT 認証で取得した現在のユーザー (`cur_user`) の `id` を Item に紐付けることで、「誰が登録した Item か」を管理している。

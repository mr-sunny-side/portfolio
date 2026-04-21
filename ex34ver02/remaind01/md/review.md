# コードレビュー: ex34_02

## バグ・エラー（要修正）

### 1. `create_engine()` の引数なし — `main.py:40`

```python
# NG
engine = create_engine()

# OK
engine = create_engine("postgresql://kimera:secret@localhost/ex34")
```

接続文字列がないため、実行時に即クラッシュします。`.env` から読み込む場合は `os.getenv("DATABASE_URL")` などを渡してください。

---

### 2. `jwt.decode` / `jwt.encode` の `algorithms` 引数 — `main.py:82, 97`

```python
# NG
token = jwt.encode(copy_sub, KEY, ALGORITHM)
payload = jwt.decode(token, KEY, ALGORITHM)

# OK
token = jwt.encode(copy_sub, KEY, algorithm=ALGORITHM)
payload = jwt.decode(token, KEY, algorithms=[ALGORITHM])
```

PyJWT では `decode` の第3引数はリスト形式の `algorithms` キーワード引数が必須です。`encode` も同様にキーワード引数を使うのが明示的です。

---

### 3. リストに対して `session.delete()` を呼んでいる — `main.py:174, 200`

```python
# NG
session.delete(cur_user.items)  # items はリスト

# OK
for item in cur_user.items:
    session.delete(item)
```

`cur_user.items` はリストのため、`session.delete()` に直接渡すとエラーになります。`/users` DELETE と `/users/items` DELETE の両方で同じ問題があります。

---

### 4. `Depends()` に依存関数を渡し忘れ — `main.py:182`

```python
# NG
cur_user: Annotated[UserDB, Depends()],

# OK
cur_user: Annotated[UserDB, Depends(get_cur_users)],
```

`/users/items` POST の認証が完全にスキップされています。任意のリクエストがアイテムを追加できてしまいます。

---

### 5. `user_id` の型アノテーション欠落 — `models.py:41`

```python
# NG
user_id = Field(default=None, foreign_key="UserDB.id")

# OK
user_id: int | None = Field(default=None, foreign_key="userdb.id")
```

型アノテーションがないと SQLModel がカラムとして認識しません。また SQLModel のテーブル名参照は小文字（`userdb.id`）になるため合わせる必要があります。

---

### 6. `UserResponse` で `Relationship` を使用 — `models.py:19`

```python
# NG
class UserResponse(BaseModel):
    items: list["ItemDB"] = Relationship(back_populates="owner")

# OK
class UserResponse(BaseModel):
    items: list[ItemResponse] = []
```

`UserResponse` は `BaseModel` であり `SQLModel` ではないため、`Relationship` は使えません。レスポンス用のモデルには通常のフィールドを使い、型も `ItemResponse` にすべきです。

---

## セキュリティ上の注意

| 箇所 | 内容 |
|---|---|
| `main.py:43` | `KEY = os.getenv("SECRET_KEY")` が `None` のまま `jwt.encode/decode` に渡されると壊れます。起動時に `assert KEY, "SECRET_KEY is not set"` 等でチェックを入れてください。 |
| `main.py:144` | `/users/register` に認証がありません。本番環境では登録制限（招待制・管理者限定など）が必要な場合があります。 |

---

## 軽微な改善点

| 箇所 | 内容 |
|---|---|
| `main.py:56, 148` | `PasswordHash.recommended()` を `auth_users` と `handle_add_users` の両方で毎回生成しています。モジュールレベルで `hasher = PasswordHash.recommended()` として共有すれば効率的です。 |

---

## 修正優先度

1. `Depends(get_cur_users)` の欠落（セキュリティ）
2. `session.delete()` のリスト問題（実行時エラー）
3. `jwt.decode` の引数形式（実行時エラー）
4. `user_id` の型アノテーション（DB定義エラー）
5. `UserResponse` の `Relationship` 除去（モデル整合性）
6. `create_engine()` の接続文字列（実装待ち）

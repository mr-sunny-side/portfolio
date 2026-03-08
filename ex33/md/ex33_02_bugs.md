# ex33_02.py バグまとめ

日付: 2026-03-07
対象ファイル: `ex33/ex33_02.py`

---

## バグ一覧

### バグ1 — `ItemDB` にカラムがない（行 67-68）

```python
# 現状
class ItemDB(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
```

**問題:** `Item` には `name` と `price` があるのに、DBテーブル定義に対応するカラムがない。
**修正:** `ItemDB` に `name: str` と `price: int` フィールドを追加する。

---

### バグ2 — `connect_args` が SQLite 専用（行 72-73）

```python
# 現状
connect_args = {"check_same_thread": False}
engine = create_engine(sql_url, connect_args=connect_args)
```

**問題:** `check_same_thread` は SQLite 専用の引数。PostgreSQL に渡すとエラーになる。
**修正:** `connect_args` を削除するか、PostgreSQL 用の引数に変える。

---

### バグ3 — `Session` の大文字・小文字（行 138）

```python
# 現状
def create_session():
    with session(engine) as session:
        yield session
```

**問題:** `session(engine)` の `session` は変数名と衝突している。`Session`（クラス）で呼ぶべき。
**修正:** `with Session(engine) as session:` に変更する。

---

### バグ4 — `startup` で間違った関数を呼んでいる（行 147）

```python
# 現状
@app.on_event("startup")
def startup():
    create_engine()
```

**問題:** `create_engine()` は SQLModel のインポート済み関数であり、ここで呼ぶべきは `create_db()`。
**修正:** `create_engine()` → `create_db()` に変更する。

---

### バグ5 — Pydantic モデルをそのまま DB に追加している（行 186）

```python
# 現状
session.add(item)   # item は Item（Pydantic モデル）
```

**問題:** `session.add()` には `SQLModel` の `ItemDB` インスタンスを渡す必要がある。
**修正:** `db_item = ItemDB(**item.model_dump())` で変換してから `session.add(db_item)` する。

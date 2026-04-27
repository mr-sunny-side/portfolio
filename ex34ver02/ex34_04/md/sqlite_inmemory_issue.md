# `no such table: userdb` の原因と修正

## 原因：SQLite インメモリDBは接続ごとに別のDBになる

`sqlite://`（インメモリSQLite）は、**接続するたびに新しい空のDBが作られる**。

```
接続A（create_all）→ テーブル作成 → 接続A内にテーブルが存在する
接続B（テスト実行）→ 別の空のDB → テーブルが存在しない ← エラー
```

`conftest.py` の `create_all(engine)` はテーブルを作るが、
テスト実行時に `Session(engine)` が新しい接続を張ると、
その接続は別のDBを見てしまうため「テーブルが存在しない」になる。

---

## 修正：`StaticPool` で接続を1つに固定する

`StaticPool` を使うと、全接続が同じ1つのDBを共有する。

```python
# conftest.py

from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.pool import StaticPool  # 追加

SQLITE_URL = "sqlite://"
engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # 追加
)
```

これで `create_all` で作ったテーブルがテスト実行時にも見える。

---

## 今回発生したエラー一覧と原因まとめ

| # | エラー | 原因 | 修正 |
|---|--------|------|------|
| 1 | `collected 0 items` | テスト関数名が `test_` で始まっていない | `main` → `test_main` |
| 2 | `fixture 'client' not found` | `conftest.py` のスペルミス（`comftest.py`） | ファイル名を `conftest.py` に変更 |
| 3 | `Could not parse SQLAlchemy URL` | `DATABASE_URL = "dummy"` は無効なURL形式 | `"sqlite://"` に変更 |
| 4 | `no such table: userdb` | インメモリSQLiteは接続ごとに別DBになる | `StaticPool` を使う |

---

## エラーメッセージの読み方

長いエラーが出ても、見るべき場所は2箇所だけ：

```
# 1. 一番下 → 何が起きたか
E   sqlalchemy.exc.OperationalError: no such table: userdb

# 2. 自分のコードが出ている行 → どこで起きたか
test_main.py:5
main.py:159: in handle_add_users
```

`venv/lib/...` で始まるスタックトレースはライブラリ内部なので基本無視してよい。

# Python Web開発学習記録

> 日々の学習記録はdevブランチで行っており、各学習ごとの最終成果ができ次第mainに上げています。

---

## ex29_09: Simple HTTP Server in Python

Pythonのソケットプログラミングによるシンプルなサーバー実装です。

### 主な機能

- GET / POST対応、パス・クエリパラメータのルーティング
- 静的ファイル配信、フォームデータ・ファイルアップロード処理
- マルチスレッドによる並行処理
- パストラバーサル防止・XSS対策・タイムアウト処理

### 技術スタック

- Python 3.x（標準ライブラリのみ: socket, threading, re 等）

### 使い方

```bash
cd ex29_09
python3 ex29_09.py
# http://127.0.0.1:8080
```

### エンドポイント

- `GET /`, `/about`, `/user/<id>`, `/search?q=` - 各ページ
- `POST /` - フォームデータ処理
- `GET /static/*` - 静的ファイル配信

---

## ex31_07: FastAPI + mboxメール解析

FastAPIを用いたmboxファイルのアップロード・解析APIサーバーです。

### 主な機能

- mboxファイルを解析し、受信回数Top3ドメイン・件名・受信期間Top3ドメインをJSON返却
- 一時ファイルに保存しレスポンス後にバックグラウンドで削除

### 技術スタック

- Python 3.x / FastAPI / Pydantic / mailbox（標準ライブラリ）

### 使い方

```bash
cd ex31/ex31_07
uvicorn ex31_07:app --reload
# http://127.0.0.1:8000
```

### エンドポイント

- `GET /` - インデックス
- `POST /mbox` - mboxファイルのアップロードと解析

---

## ex32_04: FastAPI JWT認証

FastAPIを用いたJWTベースの簡易認証APIです。

### 主な機能

- Argon2ハッシュによるパスワード検証・タイミング攻撃対策の疑似検証
- HS256によるJWTトークン発行・有効期限管理
- Bearer tokenによる保護エンドポイント

### 技術スタック

- Python 3.x / FastAPI / PyJWT / pwdlib

### 使い方

```bash
cd ex32
uvicorn ex32_04:app --reload
```

### エンドポイント

- `POST /token` - ユーザー名・パスワードでJWTトークンを取得
- `GET /users/me` - トークン認証済みユーザー情報を返す

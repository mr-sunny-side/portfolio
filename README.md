# Python Web Server Portfolio

Pythonを使ったWebサーバー実装のポートフォリオです。標準ライブラリによる低レベル実装から、Flaskフレームワークを使った実践的なREST API構築まで、段階的な学習内容をまとめています。

## プロジェクト一覧

| プロジェクト | 概要 |
|---|---|
| [09_ex29](#09_ex29---自作httpサーバー) | 標準ライブラリのみでHTTPサーバーをゼロから実装 |
| [ex30_API/07_ex30](#ex30_api07_ex30---flask-rest-api) | Flaskフレームワークを使ったREST API + mboxファイル解析 |

---

## 09_ex29 - 自作HTTPサーバー

PythonのソケットプログラミングによるシンプルなHTTPサーバー実装です。GET/POSTメソッドに対応し、マルチスレッドで複数のクライアントを処理できます。

### 主な機能

- **HTTPメソッド対応**: GET / POST
- **ルーティング機能**: パスパラメータとクエリパラメータをサポート
- **静的ファイル配信**: HTML、画像、CSS、JavaScriptなどの静的ファイルを提供
- **フォームデータ処理**:
  - `application/x-www-form-urlencoded`
  - `multipart/form-data`（ファイルアップロード対応）
- **マルチスレッド対応**: 複数のクライアント接続を同時処理
- **エラーハンドリング**: 400、404、408、500エラーに対応
- **セキュリティ対策**: パストラバーサル攻撃防止、XSS対策（HTMLエスケープ）

### 技術スタック

- Python 3.x
- 標準ライブラリのみ使用（socket, threading, logging, re, urllib.parse等）

### ファイル構成

```
09_ex29/
├── 09_ex29.py      # メインサーバープログラム
├── http.py         # HTTPリクエストの解析処理
├── route.py        # ルーティングとレスポンス生成
├── error.py        # エラーハンドリング
├── config.py       # サーバー設定
└── static/         # 静的ファイル格納ディレクトリ
    ├── index.html
    ├── about.html
    └── *.jpg
```

### 使い方

```bash
# サーバー起動
cd 09_ex29
python3 09_ex29.py

# ブラウザでアクセス
# http://127.0.0.1:8080
```

### 実装されているエンドポイント

- `GET /` - インデックスページ
- `GET /about` - アバウトページ
- `GET /user/<user_id>` - ユーザーページ（動的パラメータ）
- `GET /search?q=keyword` - 検索ページ（クエリパラメータ）
- `POST /` - フォームデータ処理
- `GET /static/*` - 静的ファイル配信

### 技術的な特徴

#### リクエスト処理フロー
1. ソケット通信でHTTPリクエストを受信
2. ヘッダーとボディを分割してパース
3. ルーティングに基づいてハンドラー関数を実行
4. HTTPレスポンスを生成してクライアントに送信

#### マルチスレッド処理
各クライアント接続ごとに新しいスレッドを生成し、並行処理を実現しています。

#### セキュリティ対策
- 静的ファイル配信時のパストラバーサル攻撃防止
- HTMLエスケープによるXSS対策
- タイムアウト処理（30秒）

### 設定

[config.py](09_ex29/config.py)で以下の設定が可能です：

- `LOCAL_HOST`: バインドするホスト（デフォルト: 127.0.0.1）
- `PORT`: ポート番号（デフォルト: 8080）
- `TIMEOUT_INT`: タイムアウト秒数（デフォルト: 30.0）
- `BUFFER_SIZE`: バッファサイズ（デフォルト: 4096）
- `MAX_READ`: 最大読み込みサイズ（デフォルト: 10MB）

### 学んだこと

- Pythonソケットプログラミングの基礎
- HTTPプロトコルの仕組み（リクエスト/レスポンス構造）
- マルチスレッドプログラミング
- 正規表現を使ったルーティング実装
- セキュリティを考慮したWeb開発

---

## ex30_API/07_ex30 - Flask REST API

Flaskフレームワークを使ったREST APIサーバーです。SQLiteによる商品データのCRUD操作と、mbox形式のメールファイルを解析するエンドポイントを実装しています。

### 主な機能

- **商品管理API**: SQLiteを使ったCRUD操作
- **mboxファイル解析**: アップロードされたmboxファイルからメール統計を生成
- **日本語対応**: JSONレスポンスの文字エスケープを無効化（`ensure_ascii=False`）
- **エラーハンドリング**: 不正なJSONや存在しないIDへの対応

### 技術スタック

- Python 3.x
- Flask
- Flask-SQLAlchemy
- werkzeug
- SQLite

### ファイル構成

```
ex30_API/07_ex30/
├── 07_ex30.py      # メインサーバー（ルーティング・DB定義）
├── mbox.py         # mboxファイル解析モジュール
└── instance/
    └── 07_ex30.db  # SQLiteデータベース
```

### 使い方

```bash
# 仮想環境の有効化
cd ex30_API
source venv/bin/activate

# サーバー起動
cd 07_ex30
python3 07_ex30.py
# → http://localhost:8080 で起動
```

### 実装されているエンドポイント

#### 商品管理

| メソッド | パス | 説明 |
|---|---|---|
| `GET` | `/` | 動作確認 |
| `GET` | `/echo/<text>` | テキストをエコーバック |
| `POST` | `/items` | 商品を追加（name, price をJSONで送信） |
| `GET` | `/items` | 全商品を取得 |
| `PUT` | `/items/<id>` | 商品情報を更新 |
| `DELETE` | `/items/<id>` | 商品を削除 |

```bash
# 商品追加の例
curl -X POST http://localhost:8080/items \
  -H "Content-Type: application/json" \
  -d '{"name": "apple", "price": 100}'

# 全商品取得
curl http://localhost:8080/items
```

#### mboxファイル解析

| メソッド | パス | 説明 |
|---|---|---|
| `POST` | `/analyze/mbox` | mboxファイルをアップロードして解析 |

```bash
# mboxファイルの解析
curl -X POST http://localhost:8080/analyze/mbox \
  -F "file=@/path/to/your.mbox"
```

**レスポンス例：**
```json
{
  "top3_count_domain": [
    {"example.com": 42}
  ],
  "top3_count_subject": [
    {"週次レポート": 10}
  ],
  "top3_interval": [
    {"example.com": 365}
  ]
}
```

### mbox解析の内容（mbox.py）

アップロードされたmboxファイルから以下の統計情報を生成します：

- **top3_count_domain**: 最も多くメールを受信したドメイン TOP3
- **top3_count_subject**: 最も多かったメール件名 TOP3（全ドメイン合算）
- **top3_interval**: 最も長期間メールを受信していたドメイン TOP3（日数）

RFC 2047形式（`=?UTF-8?B?...?=` 等）でエンコードされたメール件名も正しくデコードして処理します。

### 学んだこと

- Flaskの基本的な使い方（ルーティング、リクエスト/レスポンス処理）
- Flask-SQLAlchemyを使ったORM操作
- RESTful APIの設計（HTTPメソッドとCRUDの対応）
- ファイルアップロードの処理（werkzeug の `secure_filename`）
- JSONレスポンスの文字エンコーディング設定

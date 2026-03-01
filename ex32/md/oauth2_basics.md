# FastAPI の OAuth2 / Bearer 認証 基本解説

## 1. そもそも認証とは？

API に「あなたは誰ですか？」を確認する仕組み。
認証なしだと誰でも `/items` にアクセスできてしまう。

---

## 2. Bearer トークンとは？

ログイン成功後にサーバーが発行する「通行証」のような文字列。

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

クライアントはリクエストのヘッダーにこのトークンを付けて送る。
サーバーはトークンを見て「このユーザーはOK」と判断する。

---

## 3. OAuth2 の2つのクラス（混乱の原因）

### `OAuth2PasswordBearer`（シンプル）

```python
from fastapi.security import OAuth2PasswordBearer

oauth2 = OAuth2PasswordBearer(tokenUrl="token")
```

- `tokenUrl` だけ指定すればOK
- ユーザーが **ID + パスワード** を直接送ってトークンをもらう方式
- シンプルなAPIや学習用途に向いている

### `OAuth2AuthorizationCodeBearer`（複雑）

```python
from fastapi.security import OAuth2AuthorizationCodeBearer

oauth2 = OAuth2AuthorizationCodeBearer(
    authorizationUrl="authorize",  # 必須
    tokenUrl="token"               # 必須
)
```

- `authorizationUrl` と `tokenUrl` の **両方** が必要（片方だけだとエラー）
- Google や GitHub ログインのような「外部サービス経由」の認証方式
- 内部的に「認可コード」を経由してトークンを取得する

---

## 4. 2つの違いをフローで比較

### OAuth2PasswordBearer のフロー

```
クライアント → [ID + パスワード] → /token エンドポイント → トークン発行
クライアント → [Bearer トークン] → /items など → レスポンス
```

### OAuth2AuthorizationCodeBearer のフロー

```
クライアント → [authorizationUrl] → ログイン画面（Google等）
             ← [認可コード] ←
クライアント → [認可コード] → [tokenUrl] → トークン発行
クライアント → [Bearer トークン] → /items など → レスポンス
```

---

## 5. ex32_01.py の問題と修正

### 元のコード（エラーあり）

```python
# OAuth2AuthorizationCodeBearer は authorizationUrl が必須なのに渡していない
oauth2 = OAuth2AuthorizationCodeBearer(tokenUrl="token")  # ← エラー
```

### 修正案①：クラスを変える（推奨・シンプル）

```python
from fastapi.security import OAuth2PasswordBearer

oauth2 = OAuth2PasswordBearer(tokenUrl="token")
```

### 修正案②：引数を追加する

```python
from fastapi.security import OAuth2AuthorizationCodeBearer

oauth2 = OAuth2AuthorizationCodeBearer(
    authorizationUrl="authorize",
    tokenUrl="token"
)
```

---

## 6. `Depends` の役割

```python
async def handle_items(token: Annotated[str, Depends(oauth2)]):
```

- `Depends(oauth2)` は FastAPI に「このエンドポイントを呼ぶ前に oauth2 を実行して」という指示
- `oauth2` がリクエストヘッダーから Bearer トークンを取り出す
- 取り出したトークンの文字列が `token` 変数に入ってくる
- トークンがなければ FastAPI が自動で `401 Unauthorized` を返す

---

## 7. まとめ

| クラス | 必要な引数 | 用途 |
|---|---|---|
| `OAuth2PasswordBearer` | `tokenUrl` のみ | ID/パスワード直接認証 |
| `OAuth2AuthorizationCodeBearer` | `authorizationUrl` + `tokenUrl` | Google/GitHub等の外部認証 |

学習・シンプルなAPI開発では **`OAuth2PasswordBearer`** を使うのが基本。

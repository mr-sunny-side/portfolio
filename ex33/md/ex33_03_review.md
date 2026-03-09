# ex33_03.py コードレビュー

## 概要

FastAPI + JWT + OAuth2 + SQLModel を使った認証付きREST APIの実装。

---

## 良い点

### 1. タイミング攻撃への対策
```python
if username not in fake_db:
    hasher.verify(password, DUMMY_HASH)
    return None
```
ユーザーが存在しない場合でもダミーハッシュで検証を実行している。
存在確認だけで即returnすると、レスポンス時間の差からユーザーの存在を推測される（タイミング攻撃）ため、正しい対策。

### 2. 機密情報を環境変数で管理
```python
KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
```
JWTの署名キーとアルゴリズムをハードコードせず`.env`から読み込んでいる。

### 3. モデルの責任分離
- `User` - クライアントへのレスポンス用（パスワードなし）
- `UserInDB` - DB内部用（ハッシュ付き）
- `Token` / `TokenData` - トークン用

`hashed_password`がクライアントに漏れない設計になっている。

### 4. エラーレスポンスの統一
```python
error_detail = HTTPException(
    status_code=401,
    detail="Authentication failed",
    headers={"WWW-Authenticate": "Bearer"}
)
```
トークンのデコード失敗・ユーザー不存在など複数の失敗ケースを同じエラーにまとめ、情報漏洩を防いでいる。

---

## 改善できる点

### 1. ユーザーが存在しない場合に例外が発生する
```python
# get_cur_user 内
user = UserInDB(**fake_users_db[token_data.username])
```
`token_data.username` が `fake_users_db` に存在しない場合、`KeyError` が発生してしまう。
本来は `error_detail` を raise するべき。

```python
# 修正例
user_data = fake_users_db.get(token_data.username)
if not user_data:
    raise error_detail
user = UserInDB(**user_data)
```

### 2. `@app.on_event("startup")` は非推奨
```python
@app.on_event("startup")
def start_db():
    create_db()
```
FastAPI 0.93以降、`lifespan` を使う方法が推奨されている。

```python
# 推奨の書き方
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield

app = FastAPI(lifespan=lifespan)
```

### 3. トークンの`sub`クレームの検証が不完全
```python
username = payload['sub']
if not username:
    raise error_detail
```
`payload['sub']` が存在しない場合は `KeyError` になる（`InvalidTokenError` でキャッチされないため別の500エラーになる可能性）。
`.get()` を使うとより安全。

```python
username = payload.get('sub')
if not username:
    raise error_detail
```

---

## 学習ポイント

### OAuth2 フォームデータについて
`OAuth2PasswordRequestForm` は仕様上、`application/x-www-form-urlencoded` を要求する。
`application/json` では動かない。これはOAuth2の標準仕様（RFC 6749）によるもの。

```bash
# NG
curl -H "Content-Type: application/json" -d '{"username": "...", "password": "..."}'

# OK
curl -H "Content-Type: application/x-www-form-urlencoded" -d "username=...&password=..."
```

### JWT の構造
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9   ← header (Base64)
.eyJzdWIiOiJqb2huZG9lIiwiZXhwIjoxNzc..  ← payload (Base64)
.DwVJQY15PyVKCnOCK4fRXJ9wXBhgQCGPd2m..  ← signature
```
`jwt.io` でデコードして中身を確認できる（署名の検証には秘密鍵が必要）。

### Bearer 認証の送り方
```bash
curl -H "Authorization: Bearer <token>"
#          ↑スペルミスに注意
```

---

## まとめ

| 項目 | 評価 |
|------|------|
| セキュリティ（タイミング攻撃対策） | ○ |
| 機密情報の管理 | ○ |
| モデル設計 | ○ |
| エラーハンドリングの一部 | △ |
| API仕様への準拠 | ○ |

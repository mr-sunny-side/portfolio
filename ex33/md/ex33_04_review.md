# ex33_04.py コードレビュー

## Findings

### 1. 存在しないユーザー名で 401 ではなく 500 になる可能性がある
対象: [ex33_04.py](/home/kimetenai/portfolio/ex33/ex33_04.py#L76), [ex33_04.py](/home/kimetenai/portfolio/ex33/ex33_04.py#L92)

```python
DUMMY_HASH = "dummyhash"

if username not in fake_db:
    hasher.verify(password, DUMMY_HASH)
    return None
```

`auth_user()` はタイミング攻撃対策としてダミーハッシュを検証していますが、`DUMMY_HASH` が実際のハッシュ形式ではありません。`pwdlib.verify()` は不正なハッシュ文字列を受け取ると例外になる可能性があり、その場合は「認証失敗の 401」ではなく「サーバーエラーの 500」になります。

対策:

- `DUMMY_HASH` には `pwdlib` が解釈できる正しい Argon2 ハッシュ文字列を入れる
- もしくはダミーユーザーのハッシュ済みパスワードを使い回す

### 2. `DELETE /items/{id}` の実際のレスポンスと OpenAPI 仕様がずれる
対象: [ex33_04.py](/home/kimetenai/portfolio/ex33/ex33_04.py#L236)

```python
@app.delete("/items/{id}")
async def handle_delete_items(...):
    ...
    return Response(status_code=204)
```

実行時には `204 No Content` を返しますが、デコレータ側に `status_code=204` を指定していないため、FastAPI の自動ドキュメントではこのエンドポイントが `200` 扱いになる可能性があります。実装と仕様がずれると、Swagger UI や自動生成クライアントの解釈がぶれます。

対策:

```python
@app.delete("/items/{id}", status_code=204)
async def handle_delete_items(...):
    ...
    return Response(status_code=204)
```

## Testing gaps

`PUT` / `DELETE` の追加に対して、少なくとも次の確認が必要です。

- `PUT /items/{id}` で既存 item の `name` と `price` が更新される
- 存在しない `id` に対する `PUT` が `404` を返す
- `price < 0` の `PUT` が `422` を返す
- `DELETE /items/{id}` が `204` を返す
- 削除済み `id` の `GET /items/{id}` が `404` を返す
- 存在しない `id` に対する `DELETE` が `404` を返す

## Notes

- [`ex33_04.py`](/home/kimetenai/portfolio/ex33/ex33_04.py) 自体の構文は `python3 -m py_compile` で通過しました。
- 実行環境に `pwdlib` が入っていなかったため、認証系の実ランタイム検証まではできていません。上記 1 点目はコード上のリスクとして指摘しています。

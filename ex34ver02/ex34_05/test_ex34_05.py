def test_main(client):

	# ユーザーの登録
	res = client.post(
		"/users/register",
		json={"username": "kimera", "password": "secret"}
	)
	assert res.status_code == 200
	assert res.json() == {"id": 1, "username": "kimera", "email": None, "disabled": False, "items": []}

	# 重複したユーザーの追加
	res = client.post(
		"/users/register",
		json={"username": "kimera", "password": "secret"}
	)
	assert res.status_code == 409

	# ユーザーの参照
	res = client.get("/users")
	assert res.json() == [{"id": 1, "username": "kimera", "email": None, "disabled": False, "items": []}]

	# トークンの取得
	res = client.post(
		"/token",
		data={"username": "kimera", "password": "secret"}
	)
	assert res.status_code == 200, res.json()
	token = res.json().get("access_token")

	# ユーザーアイテムの登録
	res = client.post(
		"/items/register",
		headers={"Authorization": f"Bearer {token}"},
		json={"name": "apple", "price": 300}
	)
	assert res.status_code == 200
	assert res.json() == {"id": 1, "user_id": 1, "name": "apple", "price": 300}

	# アイテムの取得
	res = client.get("/items")
	assert res.json() == [{"id": 1, "user_id": 1, "name": "apple", "price": 300}]

	# アイテムの削除
	res = client.delete(
		"/items/1",
		headers={"Authorization": f"Bearer {token}"}
	)
	assert res.status_code == 204

	# 削除できたか確認
	res = client.get("/items")
	assert res.json() == []

	# ユーザー、アイテムの一括削除
	client.post(
		"/items/register",
		headers={"Authorization": f"Bearer {token}"},
		json={"name": "apple", "price": 300}
	)
	client.delete(
		"/users",
		headers={"Authorization": f"Bearer {token}"}
	)
	res = client.get("/users")
	assert res.json() == []

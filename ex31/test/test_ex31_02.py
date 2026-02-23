from starlette.testclient import TestClient
import ex31_02
import pytest

client = TestClient(ex31_02.app)

"""
	- 毎回リストが更新されるので注意(reset_state)
	- 全リストの検証ではnoneの要素も含むので注意
"""

@pytest.fixture(autouse=True)
def	reset_state():
	ex31_02.items.clear()
	ex31_02.item_id = 0
	yield

	ex31_02.items.clear()
	ex31_02.item_id = 0

def	test_index():
	response = client.get("/")
	assert response.status_code == 200
	assert response.json() == {"message": "Hello FastAPI !"}

def test_echo():
	response = client.get("/echo/hello")
	assert response.status_code == 200
	assert response.json() == {"echo": "hello"}

def	test_add_items():
	client.post(
		"/items",
		json={"name": "apple", "price": 300}
	)

	response = client.post(
		"/items",
		json={"name": "banana", "price": 150}
	)

	assert response.status_code == 200
	data = response.json()
	assert data["name"] == "banana"
	assert data["price"] == 150
	assert data["id"] == 1

def	test_all_items():
	client.post(
		"/items",
		json={"name": "apple", "price": 300}
	)

	client.post(
		"/items",
		json={"name": "banana", "price": 150}
	)

	response = client.get("/items")

	assert response.json() == [
		{"name": "apple", "price": 300, "tax": None, "id": 0},
		{"name": "banana", "price": 150, "tax": None, "id": 1}
	]

def	test_one_items():
	client.post(
		"/items",
		json={"name": "apple", "price": 300}
	)

	client.post(
		"/items",
		json={"name": "banana", "price": 150}
	)

	response = client.get("/items/1")
	data = response.json()

	assert data["name"] == "banana"
	assert data["price"] == 150
	assert data["id"] == 1

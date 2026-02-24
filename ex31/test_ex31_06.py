from starlette.testclient import TestClient
import ex31_06
import pytest

client = TestClient(ex31_06.app)

@pytest.fixture(autouse=True)
def	reset_state():
	ex31_06.items.clear()
	ex31_06.item_id = 1
	yield

	ex31_06.items.clear()
	ex31_06.item_id = 1

def	test_index():
	response = client.get("/")
	assert response.status_code == 200
	assert response.json() == {"message": "Hello FastAPI !"}

def	test_echo():
	response = client.get("/echo/hello")
	assert response.status_code == 200
	assert response.json() == {"echo": "hello"}

def	test_add_items():
	response = client.post(
		"/items",
		json={"name": "apple", "price": 300}
	)

	assert response.status_code == 201
	assert response.json() == {"id": 1, "name": "apple", "price": 300, "tax": 0}

def	test_all_items():
	client.post(
		"/items",
		json={"name": "apple", "price": 300}
	)

	client.post(
		"/items",
		json={"name": "banana", "price": 150}
	)

	client.post(
		"/items",
		json={"name": "orange", "price": 500}
	)

	response = client.get("/items")

	assert	response.status_code == 200
	assert response.json() == [
		{"id": 1, "name": "apple", "price": 300, "tax": 0},
		{"id": 2, "name": "banana", "price": 150, "tax": 0},
		{"id": 3, "name": "orange", "price": 500, "tax": 0}
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

	client.post(
		"/items",
		json={"name": "orange", "price": 500}
	)

	response = client.get("/items/2")
	assert response.status_code == 200
	assert response.json() == {"id": 2, "name": "banana", "price": 150, "tax": 0}

def	test_error_echo():
	response = client.get("/echo")
	assert response.status_code == 404		# パスが一致しないので404

def	test_error_all():
	response = client.get("/items?limit=0")
	assert response.status_code == 422

def	test_error_add():
	response = client.post(
		'/items',
		json={"name": "", "price": 100}
	)

	assert response.status_code == 422

def	test_404_items():
	client.post(
		"/items",
		json={"name": "apple", "price": 300}
	)

	client.post(
		"/items",
		json={"name": "banana", "price":150}
	)

	client.post(
		"/items",
		json={"name": "orange", "price": 500}
	)

	response = client.get("/items")
	assert response.json() == [
		{"id": 1, "name": "apple", "price": 300, "tax": 0},
		{"id": 2, "name": "banana", "price": 150, "tax": 0},
		{"id": 3, "name": "orange", "price": 500, "tax": 0}
	]

	response = client.get("/items/4")
	assert response.status_code == 404

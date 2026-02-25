"""
	02-25: 内部のリストを利用する前提を修正

"""

from starlette.testclient import TestClient
import ex31_06
import pytest

client = TestClient(ex31_06.app)

def	test_index():
	response = client.get("/")
	assert response.status_code == 200
	assert response.json() == {"message": "Hello FastAPI !"}

def	test_echo():
	response = client.get("/echo/hello")
	assert response.status_code == 200
	assert response.json() == {"echo": "hello"}

def	test_all_items():
	response = client.post(
		"/items",
		json={"name": "apple", "price": 300}
	)

	assert response.status_code == 201
	assert response.json() == {"id": 1, "name": "apple", "price": 300, "tax": 0}

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
	response = client.get("/items/2")
	assert response.status_code == 200
	assert response.json() == {"id": 2, "name": "banana", "price": 150, "tax": 0}

def	test_error_echo():
	response = client.get("/echo")
	assert response.status_code == 404		# パスが一致しないので404

def	test_error_add():
	response = client.post(
		'/items',
		json={"name": "", "price": 100}
	)

	assert response.status_code == 422

def	test_404_items():
	response = client.get("/items/4")
	assert response.status_code == 404

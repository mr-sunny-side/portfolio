"""
	03-26:	APIの取得

"""
import httpx

def fetch_get():
	response = httpx.get("http://httpbin.org/get")
	print(f"status: {response.status_code}")
	print(f"response: {response.json()}")

def fetch_404():
	response = httpx.get("http://httpbin.org/status/404")
	if response.status_code == 404:
		print(f"status: {response.status_code}")

if __name__ == "__main__":
	fetch_get()
	fetch_404()

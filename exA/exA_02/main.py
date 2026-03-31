"""
	03-27:	githubへの接続

"""
import httpx
from dotenv import load_dotenv
import os

load_dotenv()
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]	# environは辞書
# 取得できなかった場合例外を発生させる

def main():
	owner = "mr-sunny-side"
	repo = "portfolio"
	response  = httpx.get(
		f"https://api.github.com/repos/{owner}/{repo}/commits",	# http"s"
		headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
	)

	print(f"status: {response.status_code}")

	for commit in response.json():
		date = commit["commit"]["author"]["date"]
		message = commit["commit"]["message"]
		print(f"{date} {message}")

if __name__ == "__main__":
	main()

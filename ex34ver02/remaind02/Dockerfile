# ベースとなるpython環境を指定
FROM python:3.11-slim

# コンテナ内に作業ディレクトリを指定
WORKDIR /app

# 作業DIRに依存関係ファイルをコピー
# 依存関係をインストール
# インストール内容のキャッシュはオフにして容量を確保
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# コンテナの所有権を指定のユーザーに付与
# もとの所有権はルートになっている
# UIDは慣習に従い1000以降にする
RUN useradd -m -u 1000 kimera && chown -R kimera:kimera /app
### useradd コマンド
# kimeraというユーザーを作成し、uidを1000に指定
# -m はホームディレクトリを作成
### chown コマンド
# /app内のファイルを再帰的にkimeraの所有権に指定

# 以降のコマンドとコンテナ起動時の実行ユーザーをkimeraに指定
USER kimera

COPY . .

# コンテナ起動時に実行するためのコマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# コンテナはローカルマシンと独立して存在している
# そのため、ホストは全開放で指定

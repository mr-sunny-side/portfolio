# ベースとなるpython環境を指定
FROM python:3.11-slim

# コンテナ内の作業ディレクトリを指定
WORKDIR /app

# 依存関係を作業dirにインストール
# ダウンロード内容をキャッシュするとイメージが大きくなるため
# --no-cache-dirをつける
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリのコードを/appにコピー
COPY . .

# コンテナ実行時のコマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

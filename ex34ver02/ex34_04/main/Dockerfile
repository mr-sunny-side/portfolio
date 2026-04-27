# ベースとなるpython環境
FROM python:3.11-slim

# コンテナ内に作業ディレクトリを作成
WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt

# コンテナの所有権をユーザーに委譲
RUN useradd -m -u 1000 kimera && chown -R kimera:kimera /app
USER kimera

# プロジェクト内のファイルを作業dirにコピー
COPY . .

# コンテナ起動時のコマンド
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ]

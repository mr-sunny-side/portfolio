# ベースとなるpython環境を指定
FROM python:3.11-slim

# コンテナ内に作業ディレを指定
WORKDIR /app

# 作業ディレに依存関係ファイルをコピー
COPY requirements.txt .

# 依存関係をインストール(--no-cache)
RUN pip install --no-cache -r requirements.txt

# ユーザーを作成、コンテナの所有権を委譲
RUN useradd -m -u 1000 kimera && chown -R kimera:kimera /app

# ユーザーを切り替え
USER kimera

# プロジェクトディレをコピー
COPY . .

# コンテナ起動時のコマンドを指定
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

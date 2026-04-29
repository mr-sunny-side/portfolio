# ベースとなるpython環境を指定
FROM python:3.11-slim

# コンテナ内に作業ディレを作成
WORKDIR /app

# 依存関係ファイルをコンテナにコピー
COPY requirements.txt .

# 依存関係をインストール
RUN pip install --no-cache -r requirements.txt

# プロジェクト内ファイルをコンテナにコピー
COPY . .

# 所有権をルートから委譲するユーザーを作成
RUN useradd -m -u 1000 kimera && chown -R kimera:kimera /app

# 作成したユーザーに切り替え
USER kimera

# 起動時のコマンドを指定
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ]

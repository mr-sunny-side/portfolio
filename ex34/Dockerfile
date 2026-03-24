FROM python:3.11-slim
# ベースとなる環境を指定

WORKDIR /app
# 作業ディレクトリをコンテナ内に定義

COPY requirements.txt .
RUN pip install -r requirements.txt
# 依存関係ファイルを作業dirにコピー
# 依存関係をインストール指示

COPY . .
# アプリのコードなどを全部コピー

CMD ["uvicorn", "ex34_01a.main:app", "--host", "0.0.0.0", "--port", "8000"]
# アプリの実行コマンドを定義
# コンテナはPCと切り離されているので、0.0.0.0で定義

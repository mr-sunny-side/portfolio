FROM python:3.11-slim
# linux環境のpythonをダウンロード

WORKDIR /app
# コンテナを作成

COPY requirements.txt .
# コンテナに依存関係を配置

RUN pip install -r requirements.txt
# 依存関係をダウンロード

COPY . .
# ホストのカレントをコンテナにコピー

CMD ["uvicorn", "ex34_01.main:app", "--host", "0.0.0.0", "--port", "8000"]
# コンテナの外から接続するため、0.0.0.0で実行

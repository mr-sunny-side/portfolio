from fastapi import FastAPI, UploadFile, BackgroundTasks
from pydantic import Field, BaseModel
import tempfile
import os

from mbox import mbox_main, create_json

app = FastAPI()

class Response(BaseModel):
	top3_count_domain: list
	top3_count_subject: list
	top3_interval: list

# 一時ファイルの削除関数
def cleanup(tmp_path: str):
	os.remove(tmp_path)

@app.get("/")
def handle_index():
	return {"message": "Hello FastAPI !"}

@app.post("/mbox", response_model=Response)
async def handle_mbox(
	file: UploadFile,
	back_task: BackgroundTasks
):
	# 自分のタイミングで削除するため、delete=false
	with tempfile.NamedTemporaryFile(delete=False, suffix=".mbox") as tmp:
		tmp.write(await file.read())	# IOが発生するため、awaitを記述
		tmp_path = tmp.name				# 一時ファイルのパスを保存

	# mboxファイルを解析
	result = mbox_main(tmp_path)		# バッファがフラッシュされた後にmbox関数を呼ぶ
	json_result = create_json(result)

	# バックグラウンドで削除を実行し、先に結果を返す(練習)
	back_task.add_task(cleanup, tmp_path)
	return json_result

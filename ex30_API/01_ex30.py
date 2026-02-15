from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def	index():
	return jsonify({"massage": "Hello Flask !"})	#jsonifyが自動的にjson + httpヘッダーを作成

@app.route('/ping')
def ping():
	return jsonify({"status": "ok"})

@app.route('/echo/<text>')		# 自動的に動的パラメータとして<text>が渡される
def	echo(text):
	return jsonify({"echo": text})

if __name__ == '__main__':
	app.run(port=5000, debug=True)	# 自動的にソケットの作成listenを行う(マルチスレッド)

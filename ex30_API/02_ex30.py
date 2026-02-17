from flask import Flask, jsonify, request, abort

app = Flask(__name__)

items = []
next_id = 1

@app.route('/')
def	handle_index():
	return jsonify({'message': 'Hello Flask !'})

@app.route('/ping')
def	handle_ping():
	return jsonify({'status': 'ok'})

@app.route('/echo/<text>')
def	handle_echo(text):
	return jsonify({'echo': text})

@app.route('/items', methods=['GET', 'POST'])
def	handle_items():
	"""
	# メソッドがPOSTの場合
		- リクエストデータをjsonとして受け取る(辞書)
		- 新しい辞書を作成し、受け取ったデータを保存(id込み)
		- 作った辞書をグローバルリストに保存
		- idを更新
		- 201ステータスで作成した辞書を返す(json)
	# メソッドがGETの場合
		- 保存してあるitemsを返す(json)

	"""

	global next_id
	if request.method == 'POST':
		data = request.json

		new_item = {
			'id': next_id,
			'name': data.get('name'),
			'price': data.get('price')
		}

		items.append(new_item)
		next_id += 1

		return jsonify(new_item), 201
	else:
		return jsonify(items)

@app.route('/items/<int:id>')
def	handle_id(id):
	"""
	next関数を使って、idに一致するitemを返す
		- 無ければabortで404を発生させる

	# ポイント
		- リスト内包表記だと、有無を言わさず全件検証する
		- ジェネレータだったら、nextで呼んだら一件ずつ検証 & 一致したら終わる
		- 結果は一意なので、ジェネレータのほうが効率的

	"""
	gen = (item for item in items if item.get('id') == id)	# この時点では動作していない(リスト内包表記ではないから)
	item = next(gen, None)									# ここでnextにジェネレータ式が呼ばれる

	if item is None:
		abort(404)

	return jsonify(item)

if __name__ == '__main__':
	app.run(port=8080, debug=True)

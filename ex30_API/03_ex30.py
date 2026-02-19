from flask import Flask, jsonify, request, abort
import sqlite3

"""
	02-17:	sqlの導入から
			- ファイルの作成
			- テーブルの作成
			- /itemsパスで作成した内容をinsert & commit
			- /items/intで作成した内容を返す

"""
def	init_db():
	"""
	- connectでdbを作成
	- テーブルを作成(conn.execute)
	- 変更をコミット
	- クローズ

	"""

	conn = sqlite3.connect('03_ex30.db')
	conn.execute('''
		create table if not exists items (
		id		integer primary key autoincrement,
		name	text	not null,
		price	integer	not null
		)
	''')

	conn.commit()
	conn.close()

def	get_db():
	"""
	- dbに接続
	- データ形式をdict型に変更
	- 変更したdbを返す

	"""

	conn = sqlite3.connect('03_ex30.db')
	conn.row_factory = sqlite3.Row		#sql版のdictに変換
	return conn



items = []
next_id = 1

app = Flask(__name__)

@app.route('/')
def	handle_index():
	return jsonify({'message': 'hello flask !'})

@app.route('/ping')
def	handle_ping():
	return jsonify({'status': 'ok'})

@app.route('/echo/<text>')
def	handle_echo(text):
	return jsonify({'echo': text})

@app.route('/items', methods=['POST'])
def	handle_items():
	"""
	- jsonとしてデータを受取
	- dbを呼び出し
	- データを追加するためのカーソルを作成
	- カーソルでデータをinsert
	- 挿入したデータのidを受取
	- コミット、クローズ
	- 201でjsonデータをreturn

	"""
	global next_id
	data = request.json

	if not data or \
		'name' not in data or 'price' not in data:
		abort(400)

	conn = get_db()
	cursor = conn.cursor()

	cursor.execute(
		'insert into items (name, price) values (?, ?)',
		(data['name'], data['price'])
	)

	new_id = cursor.lastrowid

	conn.commit()
	conn.close()

	return jsonify({'id': new_id, 'name': data['name'], 'price': data['price']}), 201


@app.route('/items', methods=['GET'])
def	handle_all_items():
	conn = get_db()
	cursor = conn.cursor()
	cursor.execute('select * from items')

	rows = cursor.fetchall()
	conn.close()

	return jsonify([dict(row) for row in rows])

@app.route('/items/<int:id>', methods=['GET'])
def	handle_id(id):
	"""
	- dbを取得
	- カーソルを作成
	- カーソルでidのレコードを呼び出し
	- カーソルでfetchoneでレコードを取得
	- close
	- レコードが空なら404
	- sqlのレコード形式を辞書に変換してreturn

	"""
	conn = get_db()
	cursor = conn.cursor()
	cursor.execute('select * from items where id = ?', (id, ))

	row = cursor.fetchone()
	conn.close()

	if not row:
		abort(404)

	return jsonify(dict(row))



if __name__ == '__main__':
	init_db()
	app.run(port=8080, debug=True)

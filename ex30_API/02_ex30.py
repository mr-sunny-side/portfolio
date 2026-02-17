#!/usr/bin/env python

from flask import Flask, jsonify

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
@app.route('/items/<int:id>')
def	handle_id():
	"""
	next関数を使って、idに一致するitemを返す
		- 無ければabortで404を発生させる

	"""

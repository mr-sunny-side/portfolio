from flask import Flask, jsonify, abort, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

from mbox import mbox_main, create_json

"""
	02-20:	- 統合

"""
app = Flask(__name__)
app.json.ensure_ascii = False	# jsonが日本語をエスケープするのを拒否
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///07_ex30.db'
db = SQLAlchemy(app)

class Item(db.Model):
	id		= db.Column(db.Integer, primary_key=True)
	name	= db.Column(db.String(100), nullable=False)
	price	= db.Column(db.Integer, nullable=True)

	def	to_dict(self):
		return {'id': self.id, 'name': self.name, 'price': self.price}

# エラーハンドラー
@app.errorhandler(400)
def	handle_json_error(e):
	return jsonify({'ERROR': 'Invalid json format'})

@app.route('/')
def	handle_index():
	return jsonify({'message': 'hello flask !'})

@app.route('/echo/<text>')
def	handle_echo(text):
	return jsonify({'echo': text})

@app.route('/items', methods=['POST'])
def	handle_add_items():
	data = request.json
	if not data or \
		'name' not in data or 'price' not in data:
		abort(400)
	elif data['name'] == "" or data['price'] < 0:
		abort(400)

	item = Item(name=data['name'], price=data['price'])
	db.session.add(item)
	db.session.commit()
	return jsonify(item.to_dict()), 201

@app.route('/items', methods=['GET'])
def	handle_all_items():
	items = Item.query.all()
	return jsonify([item.to_dict() for item in items])

@app.route('/items/<int:id>', methods=['DELETE', 'PUT'])
def	handle_change_items(id):
	item = Item.query.get_or_404(id)

	if request.method == 'DELETE':
		db.session.delete(item)
		db.session.commit()
		return jsonify({id: 'deleted'})
	elif request.method == 'PUT':
		data = request.json
		if not data or \
			'name' not in data or 'price' not in data:
			abort(400)
		elif data['name'] == "" or data['price'] < 0:
			abort(400)

		item.name = data['name']
		item.price = data['price']
		db.session.add(item)
		db.session.commit()
		return jsonify(item.to_dict())

@app.route('/analyze/mbox', methods=['POST'])
def	handle_mbox():
	# fileフィールドの存在を確認
	if 'file' not in request.files:
		return jsonify({'ERROR': 'File field is not exist'}), 400

	# fileフィールドを取り出し
	file = request.files['file']

	# file名が空白でないか確認
	if file.filename == "":
		return jsonify({'ERROR': 'File name is empty'})

	# ファイル名を安全化して取り出し
	filename = secure_filename(file.filename)

	# uploadsディレクトリを作成
	os.makedirs('uploads', exist_ok=True)

	# ファイルパスをuploads下に変更
	filepath = os.path.join('uploads', filename)

	# ファイルを保存
	file.save(filepath)

	result = mbox_main(filepath)
	json_result = create_json(result)

	# 終わったら削除
	os.remove(filepath)

	return jsonify(json_result)

if __name__ == '__main__':
	with app.app_context():
		db.create_all()
	app.run(port=8080, debug=True)

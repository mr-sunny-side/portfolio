from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy

"""
	02-19:	notionで概念の復習から

"""

app = Flask(__name__)


"""
	app.config
	- flaskの設定辞書
	- sqliteでどのファイルを使うかを定義(この時点ではファイルは作られない)
	- //の後にホスト名, /の後にファイル名を入れる
	- この場合はファイルなのでホスト名は空

	db = SQLAlchemy(app)
	- app.configでファイルのシンボルを登録済み
	- 設定を読み込んで、データベースの雛形を作成する
	- 基本的にはこのオブジェクトでデータベースにアクセスする
"""
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///04_ex30.db'
db = SQLAlchemy(app)

"""
	class Item(db.Model)
	- db.Modelを渡すことで、DBの操作機能をこのクラスに引き継ぐ
	- また、カラムの定義をクラス内で行うことができる
	- コンストラクタはdb.Modelの中で定義されている
"""
class Item(db.Model):
	__tablename__ = 'items'

	id		= db.column(db.Integer, primary_key=True)	# int型のカラムを作成、primary_keyに設定
	name	= db.column(db.String(100), nullable=False) # string型で作成。intは文字数だが、ただの目安
	price	= db.column(db.Integer, nullable=False)

	def	to_dict(self):
		return ({"id": self.id, "name": self.name, "price": self.price})

@app.route('/')
def	handle_index():
	return jsonify({"message": "hello flask !"})

@app.route('/ping')
def	handle_ping():
	return jsonify({"status": "ok"})

@app.route('/echo/<text>')
def	handle_echo(text):
	return jsonify({"echo": text})

@app.route('/items', methods=['POST'])
def	handle_items():
	data = request.json

	if not data or \
		"name" not in data or "price" not in data:
		abort(400)

	# 1行分のデータを作成
	new_item = Item(name=data['name'], price=data['price'])

	# セッションに追加(git add的な操作)
	db.session.add(new_item)

	# コミット
	db.session.commit()

	return jsonify(new_item.to_dict()), 201

@app.route('/items', methods=['GET'])
def	handle_all_items():
	# Itemに紐付けられたitemsテーブルから、すべてのカラムを呼び出す
	# 返す型はItemオブジェクトのリスト
	items = Item.query.all()
	return jsonify([item.to_dict() for item in items])

@app.route('/items/<int:id>', methods=['GET'])
def	handle_pick_items(id):
	# 存在しない場合自動で404を返す
	item = Item.query.get_or_404(id)
	return jsonify(item.to_dict())

if __name__ == '__main__':
	# アプリの文脈下でしかdbは操作できない
	with app.app_context():	# これがよくわからない
		db.create_all()		# db.Modelを継承したクラスを探してテーブルを作成
	app.run(port=8080, debug=True)

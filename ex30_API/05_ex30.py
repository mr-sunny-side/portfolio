from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URL'] = 'sqlite:///05_ex30.db'
db = SQLAlchemy(app)

class Item(db.Model):
	# ここで定義しているのは全インスタンス共有のカラム構造
	# なのでselfで固有の定義はしない
	id		= db.Column(db.Integer, primary_key=True)
	name	= db.Column(db.String(100), nullable=False)
	price	= db.Column(db.Integer, nullable=False)

	def	to_dict(self):
		return {'id': self.id, 'name': self.name, 'price':self.price}

@app.route('/')
def	handle_index():
	return jsonify({'message': 'hello flask !'})

@app.route('/echo/<text>')
def	handle_echo(text):
	return jsonify({'echo': text})

@app.route('/items', methods=['POST'])
def	handle_items():
	data = request.json

	if not data or \
		'name' not in data or 'price' not in data:
		abort(400)

	# コンストラクタにカラム情報を渡して、一行分のデータを作成
	new_item = Item(name=data['name'], price=data['price'])

	# データをステージ・コミット
	db.session.add(new_item)
	db.session.commit()

	return jsonify(new_item.to_dict()), 201

@app.route('/items', methods=['GET'])
def	handle_all_items():
	items = Item.query.all()
	return jsonify([item.to_dict() for item in items])

@app.route('/items/<int:id>', methods=['GET'])
def	handle_one_item(id):
	item = Item.query.get_or_404(id)
	return jsonify(item.to_dict())

if __name__ == '__main__':
	with app.app_context():
		db.create_all()
	app.run(port=8080, debug=True)

from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy

"""
	02-19:	05_ex30の復習から - 完了
			06_ex30の機能追加から

"""
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///06_ex30.db'
db = SQLAlchemy(app)

class Item(db.Model):
	id		= db.Column(db.Integer, primary_key=True)
	name	= db.Column(db.String(100), nullable=False)
	price	= db.Column(db.Integer, nullable=False)

	def	to_dict(self):
		return {'id': self.id, 'name': self.name, 'price': self.price}

@app.route('/')
def	handle_index():
	return jsonify({'message': 'hello flask !'})

@app.route('/echo/<text>')
def	handle_echo(text):
	return jsonify({'echo': text})

@app.route('/items', methods=['POST'])
def	create_items():
	data = request.json

	if not data or \
		'name' not in data or 'price' not in data:
		abort(400)

	# レコードを作成
	item = Item(name=data['name'], price=data['price'])
	db.session.add(item)
	db.session.commit()
	return jsonify(item.to_dict()), 201

@app.route('/items', methods=['GET'])
def	handle_all_items():
	items = Item.query.all()
	return jsonify([item.to_dict() for item in items])

@app.route('/items/<int:id>', methods=['GET'])
def	handle_one_items(id):
	item = Item.query.get_or_404(id)
	return jsonify(item.to_dict())

@app.route('/items/<int:id>', methods=['DELETE', 'PUT'])
def	change_items(id):
	item = Item.query.get_or_404(id)

	if request.method == 'DELETE':
		db.session.delete(item)
		db.session.commit()
		return jsonify({id: 'DELETE'})
	elif request.method == 'PUT':
		data = request.json
		if not data or \
			'name' not in data or 'price' not in data:
			abort(400)

		item.name = data['name']
		item.price = data['price']

		db.session.add(item)
		db.session.commit()
		return jsonify(item.to_dict())

if __name__ == '__main__':
	with app.app_context():
		db.create_all()
	app.run(port=8080, debug=True)

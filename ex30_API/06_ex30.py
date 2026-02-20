from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy

"""
	02-19: 05_ex30の復習から

"""
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///06_ex30.db'
db = SQLAlchemy(app)

if __name__ == '__main__':
	with app.app_context():
		db.create_all()

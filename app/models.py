from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(120), index=True, unique=True)
	username = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	_isadmin = db.Column(db.Integer)
	books = db.relationship('Book', backref='user', lazy='dynamic')
	comments = db.relationship('Comment', backref='user', lazy='dynamic')

	def is_admin(self):
		return self._isadmin

	def set_user(self):
		self._isadmin = 0
		
	def set_admin(self):
		self._isadmin = 1

	def __repr__(self):
		return '<User {}, {}>'.format(self.email, self.username)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)


class Book(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(512), index=True)
	author = db.Column(db.String(512), index=True)
	category = db.Column(db.String, index=True)
	description = db.Column(db.String)
	src = db.Column(db.String(512))
	date = db.Column(db.String)
	views = db.Column(db.Integer)

	comments = db.relationship('Comment', backref='book', lazy='dynamic')
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	username = db.Column(db.String, index=True)

	comments_counter = db.Column(db.Integer)
	votes = db.Column(db.Integer)
	liked = db.relationship('BookVote', backref='book', lazy='dynamic')

class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	content = db.Column(db.String, index=True)
	date = db.Column(db.String)
	username = db.Column(db.String, index=True)
	votes = db.Column(db.Integer)
	book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
	liked = db.relationship('CommentVote', backref='comment', lazy='dynamic')

class BookVote(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	book_id = db.Column(db.Integer, db.ForeignKey('book.id'))

class CommentVote(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))

@login.user_loader
def load_user(id):
	return User.query.get(int(id))













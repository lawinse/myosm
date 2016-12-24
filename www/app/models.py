# -*- coding:utf-8 -*- 
from app import db

class User(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	nickname = db.Column(db.String(64), index = True, unique = True)
	email = db.Column(db.String(120), index = True, unique = True)
	posts = db.relationship('History', backref='author', lazy='dynamic')

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		try:
			return unicode(self.id) # python2
		except:
			return str(self.id) # python3
	
	def __repr__(self):
		return '<User %r>' % (self.nickname)

class History(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	body = db.Column(db.String(540))
	timestamp = db.Column(db.DateTime)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<History %r %r>' % (self.body, str(timestamp))


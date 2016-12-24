# -*- coding:utf-8 -*- 
import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from config import basedir

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
# lm.login_view = 'login'
oid = OpenID(app, os.path.join(basedir, 'tmp'))

from app import myosm
agent = myosm.myQuery
print "[app:__init__] agent built..."

from app import views, models
print "[app:__init__] views, models import..."

from flask import Flask 
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://root:pass@localhost/reading_list_db'
db = SQLAlchemy(app)

# class Example(db.Model):
# 	__tablename__ = 'example'
# 	id = db.Column('id', db.Integer, primary_key=True)
# 	data = db.Column('data', db.Unicode)

from models import Result

@app.route('/')
def hello():
    return "Hello World!"


@app.route('/<name>')
def hello_name(name):
    return "Hello {}!".format(name)


if __name__ == '__main__':
    app.run()
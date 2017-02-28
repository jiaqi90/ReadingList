from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://root:pass@localhost/reading_list_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String())
    book_lists = db.relationship('BookList')

association_table = db.Table('book_list_identifier',
    db.Column('book_list_id', db.Integer, db.ForeignKey('book_list.id')),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'))
)

class BookList(db.Model):
    __tablename__ = 'book_list'

    id = db.Column(db.Integer, primary_key=True)
    private_list = db.Column(db.Boolean(), unique=False, default=False);
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    books = db.relationship("Book", secondary=association_table, backref = db.backref('book_list', lazy = 'dynamic'))

class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    author = db.Column(db.String())
    category = db.Column(db.String())
    cover_url = db.Column(db.String())
    summary = db.Column(db.String())


#import pdb;pdb.set_trace()

@app.route('/')
def hello():
    return json.dumps({'res': "Hello World!"})


@app.route('/<name>')
def hello_name(name):
    return "Hello {}!".format(name)


if __name__ == '__main__':
    manager.run()
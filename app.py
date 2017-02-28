from flask import Flask 
from flask import request
from flask import jsonify
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

book_list_identifier = db.Table('book_list_identifier',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id')),
    db.Column('book_list_id', db.Integer, db.ForeignKey('book_list.id'))
)

class BookList(db.Model):
    __tablename__ = 'book_list'

    id = db.Column(db.Integer, primary_key=True)
    private_list = db.Column(db.Boolean(), unique=False, default=False);
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #books = db.relationship("Book", secondary=book_list_identifier, backref = db.backref('booklist', lazy = 'dynamic'))

class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    author = db.Column(db.String())
    category = db.Column(db.String())
    cover_url = db.Column(db.String())
    summary = db.Column(db.String())
    booklists = db.relationship("BookList", secondary=book_list_identifier, backref = db.backref('booklist', lazy = 'dynamic'))


#import pdb;pdb.set_trace()

@app.route('/')
def hello():
    return json.dumps({'res': "Hello World!"})

# @app.route('/<name>')
# def hello_name(name):
#     return "Hello {}!".format(name)

#GET all the books
@app.route('/books', methods=['GET'])
def getBooks():  
    data = Book.query.all()
    data_all = []
    for book in data:
        data_all.append([book.title, book.author, book.category, book.cover_url, book.summary])
    return jsonify(books=data_all)

#only able to create books for now, don't let users delete books since they may be in other people's list
#all the exceptions
@app.route('/books', methods = ['POST'])
def create_book():
    if not request.get_json or not 'title' in request.json or not 'author' in request.json or not 'category' in request.json or not 'cover_url' in request.json or not 'summary' in request.json:
        return jsonify({'Error': "Missing Parameters"}), 400
        #response.status_code = 400
        #return status_code
    elif len(request.get_json()["summary"]) < 140:
        return jsonify({'Value Error': "Min Length Summary Not Reached"}), 400

    title = request.get_json()["title"]
    author = request.get_json()["author"]
    category = request.get_json()["category"]
    cover_url = request.get_json()["cover_url"]
    summary = request.get_json()["summary"]

    newBook = Book(title = title, author = author, category = category, cover_url = cover_url, summary = summary)
    try:
        db.session.add(newBook)
        db.session.commit()
    except:
        db.session.rollback();
        db.session.flush();
        return jsonify({'Error': "DB Error"}), 400

    data = Book.query.filter_by(id=newBook.id).first()

    result = [data.title, data.author, data.category, data.cover_url, data.summary]
    return jsonify(book=result), 200


@app.route('/users', methods = ['POST'])
def create_user():
    if not request.get_json or not 'url' in request.json:
        return jsonify({'Error': "Missing Parameters"}), 400

    url = request.get_json()["url"]

    newUser = User(url = url)
    try:
        db.session.add(newUser)
        db.session.commit()
    except:
        db.session.rollback();
        db.session.flush();
        return jsonify({'Error': "DB Error"}), 400

    data = User.query.filter_by(id=newUser.id).first()

    result = [data.url]
    return jsonify(user=result), 200


@app.route('/booklist', methods = ['POST'])
def create_booklist():
    if not request.get_json or not 'private_list' in request.json or not 'user_id' in request.json:
        return jsonify({'Error': "Missing Parameters"}), 400

    private_list = request.get_json()["private_list"]
    user_id = request.get_json()["user_id"]

    new_book_list = BookList(private_list = private_list, user_id = user_id)
    try:
        db.session.add(new_book_list)
        db.session.commit()
    except:
        db.session.rollback();
        db.session.flush();
        return jsonify({'Error': "DB Error"}), 400

    data = BookList.query.filter_by(id=new_book_list.id).first()

    result = [data.private_list, data.user_id]
    return jsonify(user=result), 200

    # #GET all the public booklists
    # @app.route('/booklist', methods=['GET'])
    # def getPublicBooks():  
    #     data = BookList.query.all()
    #     data_all = []
    #     for bookList in data:
    #         if bookList.private_id:
    #             bookData = Book.query.filter_by(id=bookList.user_id).first()
    #         data_all.append([book.title, book.author, book.category, book.cover_url, book.summary])
    #     return jsonify(books=data_all)

@app.route('/booklist/<book_list_id>', methods = ['POST'])
def add_book(book_list_id):
    if not request.get_json or not 'book_id' in request.json:
        return jsonify({'Error': "Missing Parameters"}), 400

    book_id = request.get_json()["book_id"]

    book_list_data = BookList.query.filter_by(id=book_list_id).first()
    book_data = Book.query.filter_by(id=book_id).first()

    try:
        book_list_data.booklist.append(book_data)
        db.session.commit()
    except:
        db.session.rollback();
        db.session.flush()
        return jsonify({'Error': "DB Error"}), 400

    result = [];
    for book in book_list_data.booklist:
        result.append([book.title, book.author, book.category, book.cover_url, book.summary])
    return jsonify(user=result), 200

if __name__ == '__main__':
    manager.run()
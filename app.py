
from functools import wraps
from flask import request, Response
from flask import Flask 
from flask import request
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import bcrypt
import json
import jwt

SECRET = 'a_secret'

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
    username = db.Column(db.String(255))
    password_hash = db.Column(db.String(255))
    book_lists = db.relationship("BookList", backref = db.backref('booklist'))

    def serialize(self):
        return {'id': self.id, 'username': self.username, 'book_lists': [book_list.serialize() for book_list in self.book_lists]}

book_list_identifier = db.Table('book_list_identifier',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id')),
    db.Column('book_list_id', db.Integer, db.ForeignKey('book_list.id'))
)

class BookList(db.Model):
    __tablename__ = 'book_list'

    id = db.Column(db.Integer, primary_key=True)
    private_list = db.Column(db.Boolean(), unique=False, default=False);
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    books = db.relationship("Book", secondary=book_list_identifier, backref = db.backref('book_list', lazy = 'dynamic'))

    def serialize(self):
        return {'id': self.id, 'private_list': self.private_list, 'user_id': self.user_id}

class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    author = db.Column(db.String())
    category = db.Column(db.String())
    cover_url = db.Column(db.String())
    summary = db.Column(db.String())
    booklists = db.relationship("BookList", secondary=book_list_identifier, backref = db.backref('book_list', lazy = 'dynamic'))

    def serialize(self):
        return {'id': self.id, 'title': self.title, 'author': self.author, 'category': self.category, 
            'cover_url': self.cover_url, 'summary': self.summary}


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if auth == None:
            return Response('Invalid auth', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        try:
            payload = jwt.decode(auth, SECRET, algorithms=['HS256'])
            kwargs['user_id'] = payload['user_id']
        except:
            return Response('Invalid auth', 401)
        return f(*args, **kwargs)
    return decorated


@app.route('/books', methods=['GET'])
def getBooks(*args, **kwargs):
    data = Book.query.all()
    data_all = []
    for book in data:
        data_all.append([book.title, book.author, book.category, book.cover_url, book.summary])
    return jsonify(books=[e.serialize() for e in data])

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

    return jsonify(book=newBook.serialize()), 200


@app.route('/login', methods = ['POST'])
def login():
    data = request.get_json()

    username = data.get('username', None)
    password = data.get('password', None)

    if username == None or password == None:
        return jsonify({'Error': "Missing Parameters"}), 400

    user = User.query.filter(User.username == username).first()
    
    if user == None:
        return jsonify({'Error': "No such user"}), 400

    is_user = bcrypt.checkpw(str(password), str(user.password_hash))

    if not is_user:
        return jsonify({'Error': "Invalid login."}), 400
    
    token = jwt.encode({'user_id': user.id}, SECRET, algorithm='HS256')

    return jsonify({'token': token})

@app.route('/users', methods = ['GET'])
def get_users():
    return jsonify(data = [user.serialize() for user in User.query.all()])


@app.route('/users', methods = ['POST'])
def create_user():
    data = request.get_json()

    username = data.get('username', None)
    password = data.get('password', None)

    if username == None or password == None:
        return jsonify({'Error': "Missing Parameters"}), 400
    
    password_hash = bcrypt.hashpw(str(password), bcrypt.gensalt())

    newUser = User(username = username, password_hash = password_hash)

    try:
        db.session.add(newUser)
        db.session.commit()
    except:
        db.session.rollback();
        db.session.flush();
        return jsonify({'Error': "DB Error"}), 400

    return jsonify(user=newUser.serialize()), 200

@app.route('/booklist/private', methods = ['GET'])
@requires_auth
def get_private_booklist(*args, **kwargs):
    user = User.query.filter(User.id == kwargs.get('user_id', 0)).first()
    booklists = [book_list for book_list in user.book_lists if book_list.private_list == True]

    return jsonify(data = [book_list.serialize() for book_list in user.book_lists])

@app.route('/booklist', methods = ['GET'])
@requires_auth
def get_booklist(*args, **kwargs):
    books = BookList.query.filter(or_(BookList.private_list == False, BookList.user_id == kwargs.get('user_id')))

    return jsonify(data = [book_list.serialize() for book_list in books])

@app.route('/booklist', methods = ['POST', 'DELETE'])
@requires_auth
def create_delete_booklist(*args, **kwargs):
    if request.method == 'POST':
        if not request.get_json or not 'private_list' in request.json or not 'user_id' in kwargs:
            return jsonify({'Error': "Missing Parameters"}), 400

        private_list = request.get_json()["private_list"]
        user_id = kwargs.get('user_id')

        new_book_list = BookList(private_list = private_list, user_id = user_id)
        try:
            db.session.add(new_book_list)
            db.session.commit()
        except:
            db.session.rollback();
            db.session.flush();
            return jsonify({'Error': "DB Error"}), 400

        return jsonify(data=new_book_list.serialize()), 200
    elif request.method == 'DELETE':
        if not request.get_json or not 'private_list' in request.json or not 'user_id' in kwargs or not 'id' in request.json:
            return jsonify({'Error': "Missing Parameters"}), 400

        private_list = request.get_json()["private_list"]
        user_id = kwargs.get('user_id')
        list_id = request.get_json()["id"]
        delete_book_list = BookList.query.filter_by(user_id = user_id)
        found = false;
        for potential_book_list in delete_book_list:
            if potential_book_list.id == list_id:
                found = true
                break;

        if(found == False):
            return jsonify({'Error': "No Permissions"}), 400
        try: 
            BookList.query.filter_by(id=book_list_id).delete() 
            db.session.commit();
        except:
            return jsonify( { 'Error': "Failed to Delete BookList" } )

        return jsonify( { 'result': True } )
    

#Add a book to a booklist
@app.route('/booklist/<book_list_id>', methods = ['POST'])
def add_book(book_list_id):
        if not request.get_json or not 'book_id' in request.json:
            return jsonify({'Error': "Missing Parameters"}), 400

        book_id = request.get_json()["book_id"]

        book_list_data = BookList.query.filter_by(id=book_list_id).first()
        book_data = Book.query.filter_by(id=book_id).first()

        try:
            book_data.booklists.append(book_list_data)
            db.session.commit()
        except:
            db.session.rollback();
            db.session.flush()
            return jsonify({'Error': "DB Error"}), 400

        return jsonify(booklist = book_list_data.serialize()), 200

if __name__ == '__main__':
    manager.run()
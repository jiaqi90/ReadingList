from functools import wraps
from flask import request, Response, Flask, jsonify
import bcrypt
import json
import jwt
from sqlalchemy import or_, and_

from config import app, manager, db, SECRET

from models import User, BookList, Book

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
@requires_auth
def getBooks(*args, **kwargs):
    data = Book.query.all()
    data_all = []
    for book in data:
        data_all.append([book.title, book.author, book.category, book.cover_url, book.summary])
    return jsonify(books=[e.serialize() for e in data])

@app.route('/books', methods = ['POST'])
@requires_auth
def create_book(*args, **kwargs):
    if not request.get_json:
        return jsonify({'Error': "Missing Parameters"}), 400

    book_data = request.get_json()

    title = book_data.get("title")
    isbn = book_data.get("isbn")
    author = book_data.get("author")
    category = book_data.get("category")
    cover_url = book_data.get("cover_url")
    summary = book_data.get("summary")

    newBook = Book(title = title, isbn = isbn, author = author, category = category, cover_url = cover_url, summary = summary)
    try:
        db.session.add(newBook)
        db.session.commit()
    except:
        db.session.rollback();
        db.session.flush();
        return jsonify({'Error': "DB Error"}), 400

    return jsonify(book=newBook.serialize()), 200

@app.route('/books/<book_id>', methods = ['GET', 'PUT'])
@requires_auth
def update_book(book_id, *args, **kwargs):
    try:
        book = Book.query.filter_by(id=book_id).first()
        if book == None:
            return jsonify({'Error': "Book not found"}), 404

        if request.method == 'GET':
            return jsonify(data=book.serialize()), 200
        elif request.method == 'PUT':
            book_data = request.get_json()

            book.title = book_data.get('title', book.title)
            book.isbn = book_data.get('isbn', book.isbn)
            book.author = book_data.get('author', book.author)
            book.category = book_data.get('category', book.category)
            book.cover_url = book_data.get('cover_url', book.cover_url)
            book.summary = book_data.get('summary', book.summary)
            db.session.commit()

            return jsonify(data=book.serialize()), 200
    except:
        return jsonify({'Error': "Failed to Update Book" })



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

@app.route('/booklist', methods = ['GET'])
@requires_auth
def get_booklist(*args, **kwargs):
    books = BookList.query.filter(or_(BookList.private_list == False, BookList.user_id == kwargs.get('user_id')))\

    return jsonify(data = [book_list.serialize() for book_list in books])


@app.route('/booklist', methods = ['POST'])
@requires_auth
def create_booklist(*args, **kwargs):
    if not request.get_json or not 'user_id' in kwargs:
        return jsonify({'Error': "Missing Parameters"}), 400

    private_list = request.get_json().get("private_list")
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

@app.route('/booklist', methods = ['PUT'])
@requires_auth
def update_booklist(*args, **kwargs):
    if not request.get_json or not 'private_list' in request.json or not 'user_id' in kwargs or not 'id' in request.json:
        return jsonify({'Error': "Missing Parameters"}), 400

    private_list = request.get_json()["private_list"]
    user_id = kwargs.get('user_id')
    list_id = request.get_json()["id"]
    update_book_list = BookList.query.filter_by(user_id = user_id)
    found = False
    for potential_book_list in update_book_list:
        if potential_book_list.id == list_id:
            found = True
            break

    if(found == False):
        return jsonify({'Error': "No Permissions"}), 400

    try:
        book_list = BookList.query.filter_by(id=list_id).first()
        book_list.private_list = private_list;
        db.session.commit();
    except:
        return jsonify( { 'Error': "Failed to Update BookList" } )

    return jsonify(data=book_list.serialize())

@app.route('/booklist', methods = ['DELETE'])
@requires_auth
def delete_booklist(*args, **kwargs):
    if request.method == 'DELETE':
        if not request.get_json or not 'private_list' in request.json or not 'user_id' in kwargs or not 'id' in request.json:
            return jsonify({'Error': "Missing Parameters"}), 400

        private_list = request.get_json()["private_list"]
        user_id = kwargs.get('user_id')
        list_id = request.get_json()["id"]
        delete_book_list = BookList.query.filter_by(user_id = user_id)
        found = False
        for potential_book_list in delete_book_list:
            if potential_book_list.id == list_id:
                found = True
                break

        if(found == False):
            return jsonify({'Error': "No Permissions"}), 400
        try: 
            BookList.query.filter_by(id=list_id).delete() 
            db.session.commit();
        except:
            return jsonify( { 'Error': "Failed to Delete BookList" } )

        return jsonify( { 'result': True } )
    
@app.route('/booklist/private', methods = ['GET'])
@requires_auth
def get_private_booklist(*args, **kwargs):
    user = User.query.filter(User.id == kwargs.get('user_id', 0)).first()
    booklists = [book_list for book_list in user.book_lists if book_list.private_list == True]

    return jsonify(data = [book_list.serialize() for book_list in user.book_lists])

#Add a book to a booklist
@app.route('/booklist/<book_list_id>/books', methods = ['POST'])
@requires_auth
def add_book(book_list_id, *args, **kwargs):
        if not request.get_json or not 'book_id' in request.json:
            return jsonify({'Error': "Missing Parameters"}), 400

        book_id = request.get_json()["book_id"]

        user_id = kwargs.get('user_id')
        user_book_list = BookList.query.filter_by(user_id=user_id).filter_by(id=book_list_id).first()

        book_data = Book.query.filter_by(id=book_id).first()

        try:
            user_book_list.books.append(book_data)
            db.session.commit()
        except:
            db.session.rollback();
            db.session.flush()
            return jsonify({'Error': "DB Error"}), 400

        return jsonify(booklist = user_book_list.serialize()), 200

@app.route('/booklist/<book_list_id>/books/<book_id>', methods = ['DELETE'])
@requires_auth
def delete_book(book_list_id, book_id, *args, **kwargs):
    book_list = BookList.query.filter_by(id=book_list_id).first()
    book = Book.query.filter_by(id=book_id).first()

    try:
        if book not in book_list.books:
            return jsonify({'Error': 'Book not in list'}), 404
        
        book_list.books.remove(book)
        db.session.commit()
    except:
        db.session.rollback();
        db.session.flush()
        return jsonify({'Error': "DB Error"}), 400

    return jsonify( { 'result': True } )

if __name__ == '__main__':
    manager.run()
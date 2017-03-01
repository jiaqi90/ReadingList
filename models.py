from config import db

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
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
    private_list = db.Column(db.Boolean(), default=False);
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    books = db.relationship("Book", secondary=book_list_identifier, backref = db.backref('book_list', lazy = 'dynamic'))

    def serialize(self):
        return {'id': self.id, 'private_list': self.private_list, 'user_id': self.user_id, 'books': [b.serialize() for b in self.books]}

class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.Integer(), unique=True, nullable=False)
    title = db.Column(db.String(), nullable=False)
    author = db.Column(db.String(), nullable=False)
    category = db.Column(db.String(), nullable=False)
    cover_url = db.Column(db.String(), nullable=False)
    summary = db.Column(db.String(140), nullable=False)
    booklists = db.relationship("BookList", secondary=book_list_identifier, backref = db.backref('book_list', lazy = 'dynamic'))

    def serialize(self):
        return {'id': self.id, 'isbn': self.isbn, 'title': self.title, 'author': self.author, 'category': self.category, 
            'cover_url': self.cover_url, 'summary': self.summary}

from app import db

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
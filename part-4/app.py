from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================================================================
# MODELS
# =============================================================================

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    city = db.Column(db.String(50))
    books = db.relationship('Book', backref='author_ref', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'bio': self.bio,
            'city': self.city,
            'books_count': len(self.books) if self.books else 0
        }

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    year = db.Column(db.Integer)
    isbn = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        author = Author.query.get(self.author_id) if self.author_id else None
        return {
            'id': self.id,
            'title': self.title,
            'author_id': self.author_id,
            'author_name': author.name if author else 'Unknown',
            'year': self.year,
            'isbn': self.isbn,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# =============================================================================
# AUTHOR CRUD APIs
# =============================================================================

@app.route('/api/authors', methods=['GET'])
def get_authors():
    authors = Author.query.all()
    return jsonify({
        'success': True,
        'count': len(authors),
        'authors': [author.to_dict() for author in authors]
    })

@app.route('/api/authors/<int:id>', methods=['GET'])
def get_author(id):
    author = Author.query.get(id)
    
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    
    return jsonify({
        'success': True,
        'author': author.to_dict(),
        'books': [book.to_dict() for book in author.books]
    })

@app.route('/api/authors', methods=['POST'])
def create_author():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    if not data.get('name'):
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    
    new_author = Author(
        name=data['name'],
        bio=data.get('bio', ''),
        city=data.get('city', '')
    )
    
    db.session.add(new_author)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Author created successfully',
        'author': new_author.to_dict()
    }), 201

@app.route('/api/authors/<int:id>', methods=['PUT'])
def update_author(id):
    author = Author.query.get(id)
    
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    if 'name' in data:
        author.name = data['name']
    if 'bio' in data:
        author.bio = data['bio']
    if 'city' in data:
        author.city = data['city']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Author updated successfully',
        'author': author.to_dict()
    })

@app.route('/api/authors/<int:id>', methods=['DELETE'])
def delete_author(id):
    author = Author.query.get(id)
    
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    
    if author.books:
        return jsonify({
            'success': False, 
            'error': 'Cannot delete author with books. Delete books first.'
        }), 400
    
    db.session.delete(author)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Author deleted successfully'
    })

# =============================================================================
# BOOK CRUD APIs (Updated with Pagination & Sorting)
# =============================================================================

@app.route('/api/books', methods=['GET'])
def get_books():
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Sorting parameters
    sort_by = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')
    
    # Validate sort field
    allowed_sort_fields = ['id', 'title', 'year', 'created_at']
    if sort_by not in allowed_sort_fields:
        sort_by = 'id'
    
    # Build query
    query = Book.query
    
    # Apply sorting
    if order.lower() == 'desc':
        query = query.order_by(getattr(Book, sort_by).desc())
    else:
        query = query.order_by(getattr(Book, sort_by).asc())
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items
    
    return jsonify({
        'success': True,
        'page': page,
        'per_page': per_page,
        'total_pages': pagination.pages,
        'total_books': pagination.total,
        'sort_by': sort_by,
        'order': order,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'books': [book.to_dict() for book in books]
    })

@app.route('/api/books/<int:id>', methods=['GET'])
def get_book(id):
    book = Book.query.get(id)
    
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    
    return jsonify({
        'success': True,
        'book': book.to_dict()
    })

@app.route('/api/books', methods=['POST'])
def create_book():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    if not data.get('title'):
        return jsonify({'success': False, 'error': 'Title is required'}), 400
    
    if not data.get('author_id'):
        return jsonify({'success': False, 'error': 'author_id is required'}), 400
    
    # Check if author exists
    author = Author.query.get(data['author_id'])
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    
    # Check for duplicate ISBN
    if data.get('isbn'):
        existing = Book.query.filter_by(isbn=data['isbn']).first()
        if existing:
            return jsonify({'success': False, 'error': 'ISBN already exists'}), 400
    
    new_book = Book(
        title=data['title'],
        author_id=data['author_id'],
        year=data.get('year'),
        isbn=data.get('isbn')
    )
    
    db.session.add(new_book)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Book created successfully',
        'book': new_book.to_dict()
    }), 201

@app.route('/api/books/<int:id>', methods=['PUT'])
def update_book(id):
    book = Book.query.get(id)
    
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    if 'title' in data:
        book.title = data['title']
    if 'author_id' in data:
        book.author_id = data['author_id']
    if 'year' in data:
        book.year = data['year']
    if 'isbn' in data:
        book.isbn = data['isbn']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Book updated successfully',
        'book': book.to_dict()
    })

@app.route('/api/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get(id)
    
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    
    db.session.delete(book)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Book deleted successfully'
    })

# =============================================================================
# SEARCH APIs
# =============================================================================

@app.route('/api/books/search', methods=['GET'])
def search_books():
    query = Book.query
    
    # Filter by title
    title = request.args.get('q')
    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))
    
    # Filter by author name
    author_name = request.args.get('author')
    if author_name:
        query = query.join(Author).filter(Author.name.ilike(f'%{author_name}%'))
    
    books = query.all()
    
    return jsonify({
        'success': True,
        'count': len(books),
        'books': [book.to_dict() for book in books]
    })

# =============================================================================
# INITIALIZE DATABASE
# =============================================================================

def init_db():
    with app.app_context():
        db.create_all()
        
        # Add sample authors if none exist
        if Author.query.count() == 0:
            authors = [
                Author(name='J.K. Rowling', bio='British author', city='London'),
                Author(name='George Orwell', bio='English novelist', city='London'),
                Author(name='Agatha Christie', bio='Mystery writer', city='Torquay')
            ]
            db.session.add_all(authors)
            db.session.commit()
            print('📝 Sample authors added!')
        
        # Add sample books if none exist
        if Book.query.count() == 0:
            # Get author IDs
            authors = Author.query.all()
            
            books = [
                Book(title='Harry Potter', author_id=authors[0].id, year=1997, isbn='978-0747532743'),
                Book(title='1984', author_id=authors[1].id, year=1949, isbn='978-0451524935'),
                Book(title='Murder on the Orient Express', author_id=authors[2].id, year=1934, isbn='978-0007119318')
            ]
            db.session.add_all(books)
            db.session.commit()
            print('📚 Sample books added!')

# =============================================================================
# HOME PAGE
# =============================================================================

@app.route('/')
def index():
    return '''
    <html>
    <head><title>Library API</title></head>
    <body>
        <h1>📚 Library Management API</h1>
        <p>Backend running successfully!</p>
        <p>Use Postman to test APIs or open frontend.html</p>
        <p><a href="/api/books">Books API</a> | <a href="/api/authors">Authors API</a></p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
    print("🚀 Server running at http://localhost:5000")
"""
Part 2: Full CRUD Operations with HTML Forms
=============================================
Complete Create, Read, Update, Delete operations with user forms.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

DATABASE = 'students.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            course TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# =============================================================================
# SEARCH & READ - Display all students with optional search
# =============================================================================

@app.route('/')
def index():
    search_query = request.args.get('query', '')
    
    conn = get_db_connection()
    
    if search_query:
        students = conn.execute(
            'SELECT * FROM students WHERE LOWER(name) LIKE ? ORDER BY id DESC',
            ('%' + search_query.lower() + '%',)
        ).fetchall()
    else:
        students = conn.execute('SELECT * FROM students ORDER BY id DESC').fetchall()
    
    conn.close()
    return render_template('index.html', students=students, search_query=search_query)


# =============================================================================
# CREATE - Add new student with email validation
# =============================================================================

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']
        
        conn = get_db_connection()
        
        existing_student = conn.execute(
            'SELECT * FROM students WHERE email = ?', 
            (email,)
        ).fetchone()
        
        if existing_student:
            conn.close()
            flash('Email already exists! Please use a different email.', 'danger')
            return render_template('add.html', 
                                   name=name, 
                                   email=email, 
                                   course=course)
        
        conn.execute(
            'INSERT INTO students (name, email, course) VALUES (?, ?, ?)',
            (name, email, course)
        )
        conn.commit()
        conn.close()
        
        flash('Student added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add.html')


# =============================================================================
# UPDATE - Edit existing student with email validation
# =============================================================================

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']
        
        existing_student = conn.execute(
            'SELECT * FROM students WHERE email = ? AND id != ?', 
            (email, id)
        ).fetchone()
        
        if existing_student:
            flash('Email already exists for another student! Please use a different email.', 'danger')
            student = {'id': id, 'name': name, 'email': email, 'course': course}
            return render_template('edit.html', student=student)
        
        conn.execute(
            'UPDATE students SET name = ?, email = ?, course = ? WHERE id = ?',
            (name, email, course, id)
        )
        conn.commit()
        conn.close()
        
        flash('Student updated successfully!', 'success')
        return redirect(url_for('index'))
    
    student = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('edit.html', student=student)


# =============================================================================
# DELETE - Remove student
# =============================================================================

@app.route('/delete/<int:id>')
def delete_student(id):
    conn = get_db_connection()
    
    student = conn.execute('SELECT name FROM students WHERE id = ?', (id,)).fetchone()
    
    conn.execute('DELETE FROM students WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    if student:
        flash(f'Student "{student["name"]}" deleted!', 'danger')
    else:
        flash('Student deleted!', 'danger')
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    
    # Check if database has any students, if not add some test data
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    conn.close()
    
    if count == 0:
        print("Database is empty. Adding test students...")
        conn = get_db_connection()
        
      
        for student in test_students:
            try:
                conn.execute('INSERT INTO students (name, email, course) VALUES (?, ?, ?)', student)
            except:
                pass  # Skip if student already exists
        
        conn.commit()
        conn.close()
        print("Test students added successfully!")
    
    app.run(debug=True)
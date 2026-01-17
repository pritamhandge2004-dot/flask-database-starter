# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================================================================
# MODELS
# =============================================================================

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    courses = db.relationship('Course', backref='teacher', lazy=True)

    def __repr__(self):
        return f'<Teacher {self.name}>'


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    students = db.relationship('Student', backref='course', lazy=True)

    def __repr__(self):
        return f'<Course {self.name}>'


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'


# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def index():
    students = Student.query.all()
    return render_template('index.html', students=students)


@app.route('/courses')
def courses():
    all_courses = Course.query.all()
    return render_template('courses.html', courses=all_courses)


@app.route('/teachers')
def teachers():
    all_teachers = Teacher.query.all()
    return render_template('teachers.html', teachers=all_teachers)


# -------------------- STUDENTS CRUD --------------------

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course_id = request.form['course_id']

        new_student = Student(name=name, email=email, course_id=course_id)
        db.session.add(new_student)
        db.session.commit()

        flash('Student added successfully!', 'success')
        return redirect(url_for('index'))

    courses_list = Course.query.all()
    return render_template('add.html', courses=courses_list)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)

    if request.method == 'POST':
        student.name = request.form['name']
        student.email = request.form['email']
        student.course_id = request.form['course_id']

        db.session.commit()
        flash('Student updated!', 'success')
        return redirect(url_for('index'))

    courses_list = Course.query.all()
    return render_template('edit.html', student=student, courses=courses_list)


@app.route('/delete/<int:id>')
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()

    flash('Student deleted!', 'danger')
    return redirect(url_for('index'))


# -------------------- COURSES --------------------

@app.route('/add-course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        teacher_id = request.form.get('teacher_id')

        new_course = Course(
            name=name,
            description=description,
            teacher_id=teacher_id if teacher_id else None
        )
        db.session.add(new_course)
        db.session.commit()

        flash('Course added!', 'success')
        return redirect(url_for('courses'))

    teachers_list = Teacher.query.all()
    return render_template('add_course.html', teachers=teachers_list)


# -------------------- TEACHERS CRUD --------------------

@app.route('/add-teacher', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        new_teacher = Teacher(name=name, email=email)
        db.session.add(new_teacher)
        db.session.commit()

        flash('Teacher added successfully!', 'success')
        return redirect(url_for('teachers'))

    return render_template('add_teacher.html')


@app.route('/edit-teacher/<int:id>', methods=['GET', 'POST'])
def edit_teacher(id):
    teacher = Teacher.query.get_or_404(id)

    if request.method == 'POST':
        teacher.name = request.form['name']
        teacher.email = request.form['email']

        db.session.commit()
        flash('Teacher updated successfully!', 'success')
        return redirect(url_for('teachers'))

    return render_template('edit_teacher.html', teacher=teacher)


@app.route('/delete-teacher/<int:id>')
def delete_teacher(id):
    teacher = Teacher.query.get_or_404(id)

    # Safe delete: pehle courses unassign kar do
    for course in teacher.courses:
        course.teacher_id = None

    db.session.delete(teacher)
    db.session.commit()

    flash('Teacher deleted successfully!', 'danger')
    return redirect(url_for('teachers'))


# =============================================================================
# INITIALIZE DATABASE
# =============================================================================

def init_db():
    """Create tables and add sample data"""
    with app.app_context():
        db.create_all()

        # Add sample teachers if none exist
        if Teacher.query.count() == 0:
            teachers_list = [
                Teacher(name='Dr. Smith', email='smith@school.edu'),
                Teacher(name='Prof. Johnson', email='johnson@school.edu'),
                Teacher(name='Ms. Williams', email='williams@school.edu'),
            ]
            db.session.add_all(teachers_list)
            db.session.commit()
            print('Sample teachers added!')

        # Add sample courses if none exist
        if Course.query.count() == 0:
            all_teachers = Teacher.query.all()
            courses_list = [
                Course(
                    name='Python Basics',
                    description='Learn Python programming fundamentals',
                    teacher_id=all_teachers[0].id if all_teachers else None
                ),
                Course(
                    name='Web Development',
                    description='HTML, CSS, JavaScript and Flask',
                    teacher_id=all_teachers[1].id if len(all_teachers) > 1 else None
                ),
                Course(
                    name='Data Science',
                    description='Data analysis with Python',
                    teacher_id=all_teachers[2].id if len(all_teachers) > 2 else None
                ),
            ]
            db.session.add_all(courses_list)
            db.session.commit()
            print('Sample courses added!')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

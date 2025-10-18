from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import datetime
import os

app = Flask(__name__)

# SQLite connection
DATABASE = 'teacher_attendance.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                employee_id TEXT UNIQUE NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY (teacher_id) REFERENCES teachers (id)
            )
        ''')
        db.commit()


init_db()


@app.route('/')
def dashboard():
   
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    db = get_db()
    
    
    total_teachers = db.execute('SELECT COUNT(*) as count FROM teachers').fetchone()['count']
    

    present_count = db.execute('SELECT COUNT(*) as count FROM attendance WHERE date = ? AND status = ?', 
                              (today, 'Present')).fetchone()['count']
    absent_count = db.execute('SELECT COUNT(*) as count FROM attendance WHERE date = ? AND status = ?', 
                             (today, 'Absent')).fetchone()['count']
    leave_count = db.execute('SELECT COUNT(*) as count FROM attendance WHERE date = ? AND status = ?', 
                            (today, 'Leave')).fetchone()['count']
    
    return render_template('dashboard.html', 
                          total_teachers=total_teachers,
                          present_count=present_count,
                          absent_count=absent_count,
                          leave_count=leave_count,
                          today=today)

@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    message = ""
    if request.method == 'POST':
        name = request.form.get('name')
        department = request.form.get('department')
        employee_id = request.form.get('employee_id')
        
        db = get_db()
        
        existing_teacher = db.execute('SELECT * FROM teachers WHERE employee_id = ?', 
                                     (employee_id,)).fetchone()
        if existing_teacher:
            message = "Error: Student ID already exists!"
        else:
            
            db.execute('INSERT INTO teachers (name, department, employee_id) VALUES (?, ?, ?)',
                      (name, department, employee_id))
            db.commit()
            message = "Student added successfully!"
            
    return render_template('add_teacher.html', message=message)

@app.route('/mark_attendance')
def mark_attendance():
    db = get_db()
 
    teachers = db.execute('SELECT * FROM teachers').fetchall()
    

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    return render_template('mark_attendance.html', teachers=teachers, today=today)

@app.route('/view_attendance')
def view_attendance():
    db = get_db()
    
    date = request.args.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
    

    attendance_data = db.execute('''
        SELECT a.id, t.name as teacher_name, t.department, t.employee_id, a.status, a.note
        FROM attendance a
        JOIN teachers t ON a.teacher_id = t.id
        WHERE a.date = ?
    ''', (date,)).fetchall()
    
 
    attendance_data = [dict(row) for row in attendance_data]
    
    return render_template('view_attendance.html', attendance_data=attendance_data, selected_date=date)


@app.route('/api/teachers')
def api_teachers():
    db = get_db()
    teachers = db.execute('SELECT id, name, department, employee_id FROM teachers').fetchall()
    
    teachers_list = [dict(teacher) for teacher in teachers]
    return jsonify(teachers_list)

@app.route('/api/mark_attendance', methods=['POST'])
def api_mark_attendance():
    db = get_db()
    
    
    if request.is_json:
        data = request.json
    else:
        data = request.form
    
    teacher_id = data.get('teacher_id')
    date = data.get('date')
    status = data.get('status')
    note = data.get('note', '')
    

    existing_record = db.execute(
        'SELECT id FROM attendance WHERE teacher_id = ? AND date = ?', 
        (teacher_id, date)
    ).fetchone()
    
    if existing_record:
        
        db.execute(
            'UPDATE attendance SET status = ?, note = ? WHERE id = ?',
            (status, note, existing_record['id'])
        )
    else:
 
        db.execute(
            'INSERT INTO attendance (teacher_id, date, status, note) VALUES (?, ?, ?, ?)',
            (teacher_id, date, status, note)
        )
    
    db.commit()
    return jsonify({"success": True})

@app.route('/api/get_attendance')
def api_get_attendance():
    db = get_db()
    teacher_id = request.args.get('teacher_id')
    date = request.args.get('date')
    
    query = 'SELECT * FROM attendance WHERE 1=1'
    params = []
    
    if teacher_id:
        query += ' AND teacher_id = ?'
        params.append(teacher_id)
    if date:
        query += ' AND date = ?'
        params.append(date)
    
    attendance_records = db.execute(query, params).fetchall()
    
    
    attendance_list = [dict(record) for record in attendance_records]
    
    return jsonify(attendance_list)

if __name__ == '__main__':
    app.run(debug=True)
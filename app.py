from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key in production

# Available subjects
AVAILABLE_SUBJECTS = [
    'TCS 302', 'TCS 307', 'TCS 308', 'TMA 316', 'TCS 346',
    'XCS 301', 'PCS 302', 'PCS 307', 'PCS 308', 'PESE 300'
]

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
                employee_id TEXT NOT NULL,
                subject TEXT NOT NULL DEFAULT 'TCS 302',
                UNIQUE(employee_id, subject)  -- A teacher can be in a subject only once
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                note TEXT,
                subject TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers (id),
                UNIQUE(teacher_id, date, subject)  -- One attendance record per teacher per day per subject
            )
        ''')
        db.commit()


init_db()


@app.route('/')
def index():
    # Redirect to subject selection if no subject is selected
    if 'current_subject' not in session:
        return redirect(url_for('select_subject'))
    return redirect(url_for('dashboard'))

@app.route('/select_subject', methods=['GET', 'POST'])
def select_subject():
    if request.method == 'POST':
        subject = request.form.get('subject')
        if subject in AVAILABLE_SUBJECTS:
            session['current_subject'] = subject
            return redirect(url_for('dashboard'))
    return render_template('select_subject.html', subjects=AVAILABLE_SUBJECTS)

@app.route('/dashboard')
def dashboard():
    if 'current_subject' not in session:
        return redirect(url_for('select_subject'))
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    current_subject = session['current_subject']
    
    db = get_db()
    
    # Get total teachers for current subject
    total_teachers = db.execute('''
        SELECT COUNT(*) as count FROM teachers 
        WHERE subject = ?
    ''', (current_subject,)).fetchone()['count']
    
    # Get today's attendance for current subject
    attendance = db.execute('''
        SELECT status, COUNT(*) as count 
        FROM attendance 
        WHERE date = ? AND subject = ?
        GROUP BY status
    ''', (today, current_subject)).fetchall()
    
    # Initialize counts
    present_count = 0
    absent_count = 0
    
    for row in attendance:
        if row['status'] == 'Present':
            present_count = row['count']
        elif row['status'] == 'Absent':
            absent_count = row['count']
    
    return render_template('dashboard.html', 
                          total_teachers=total_teachers,
                          present_count=present_count,
                          absent_count=absent_count,
                          today=today,
                          current_subject=current_subject)

@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if 'current_subject' not in session:
        return redirect(url_for('select_subject'))
        
    message = ""
    if request.method == 'POST':
        name = request.form.get('name')
        department = request.form.get('department')
        employee_id = request.form.get('employee_id')
        subject = session['current_subject']
        
        db = get_db()
        
        # Check if student already exists in this subject
        existing_teacher = db.execute('''
            SELECT * FROM teachers 
            WHERE employee_id = ? AND subject = ?
        ''', (employee_id, subject)).fetchone()
        
        if existing_teacher:
            message = "Error: Student ID already exists in this subject!"
        else:
            try:
                db.execute('''
                    INSERT INTO teachers (name, department, employee_id, subject) 
                    VALUES (?, ?, ?, ?)
                ''', (name, department, employee_id, subject))
                db.commit()
                message = "Student added successfully to " + subject + "!"
            except sqlite3.IntegrityError as e:
                db.rollback()
                message = f"Error: {str(e)}"
    
    # Get all teachers for current subject
    db = get_db()
    current_subject = session['current_subject']
    teachers = db.execute('''
        SELECT * FROM teachers 
        WHERE subject = ?
        ORDER BY name
    ''', (current_subject,)).fetchall()
            
    return render_template('add_teacher.html', 
                         message=message, 
                         teachers=teachers,
                         current_subject=current_subject)

@app.route('/mark_attendance')
def mark_attendance():
    if 'current_subject' not in session:
        return redirect(url_for('select_subject'))
        
    current_subject = session['current_subject']
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    db = get_db()
    
    # Get all teachers for current subject
    teachers = db.execute('''
        SELECT t.*, a.status as attendance_status
        FROM teachers t
        LEFT JOIN attendance a ON t.id = a.teacher_id 
            AND a.date = ? 
            AND a.subject = ?
        WHERE t.subject = ?
        ORDER BY t.name
    ''', (today, current_subject, current_subject)).fetchall()
    
    # Convert SQLite Row objects to dictionaries
    teachers_list = []
    for teacher in teachers:
        teacher_dict = dict(teacher)
        teachers_list.append(teacher_dict)
    
    return render_template('mark_attendance.html', 
                         teachers=teachers_list, 
                         today=today,
                         current_subject=current_subject)

@app.route('/view_attendance')
def view_attendance():
    if 'current_subject' not in session:
        return redirect(url_for('select_subject'))
        
    current_subject = session['current_subject']
    date = request.args.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
    
    db = get_db()
    
    # Get attendance for the selected date and subject
    attendance_data = db.execute('''
        SELECT a.id, t.name as teacher_name, t.department, t.employee_id, a.status, a.note
        FROM attendance a
        JOIN teachers t ON a.teacher_id = t.id
        WHERE a.date = ? AND a.subject = ?
        ORDER BY t.name
    ''', (date, current_subject)).fetchall()
    
    attendance_data = [dict(row) for row in attendance_data]
    
    return render_template('view_attendance.html', 
                         attendance_data=attendance_data, 
                         selected_date=date,
                         current_subject=current_subject)

@app.route('/api/teachers')
def api_teachers():
    if 'current_subject' not in session:
        return jsonify({"error": "No subject selected"}), 400
        
    db = get_db()
    current_subject = session['current_subject']
    
    teachers = db.execute('''
        SELECT id, name, department, employee_id 
        FROM teachers 
        WHERE subject = ?
        ORDER BY name
    ''', (current_subject,)).fetchall()
    
    teachers_list = [dict(teacher) for teacher in teachers]
    return jsonify(teachers_list)

@app.route('/api/delete_teacher/<int:teacher_id>', methods=['DELETE'])
def api_delete_teacher(teacher_id):
    if 'current_subject' not in session:
        return jsonify({"error": "No subject selected"}), 400
        
    db = get_db()
    current_subject = session['current_subject']
    
    try:
        # Delete attendance records first (due to foreign key constraint)
        db.execute('''
            DELETE FROM attendance 
            WHERE teacher_id = ? AND subject = ?
        ''', (teacher_id, current_subject))
        
        # Then delete the teacher from this subject
        db.execute('''
            DELETE FROM teachers 
            WHERE id = ? AND subject = ?
        ''', (teacher_id, current_subject))
        
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/attendance', methods=['GET'])
def api_get_attendance():
    if 'current_subject' not in session:
        return jsonify({"error": "No subject selected"}), 400
        
    db = get_db()
    current_subject = session['current_subject']
    
    date = request.args.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
    
    # Get all teachers and their attendance for the selected date
    attendance = db.execute('''
        SELECT t.id as teacher_id, t.name, t.employee_id, a.status
        FROM teachers t
        LEFT JOIN attendance a ON t.id = a.teacher_id 
            AND a.date = ? 
            AND a.subject = ?
        WHERE t.subject = ?
        ORDER BY t.name
    ''', (date, current_subject, current_subject)).fetchall()
    
    return jsonify([dict(row) for row in attendance])

@app.route('/api/mark_attendance', methods=['POST'])
def api_mark_attendance():
    if 'current_subject' not in session:
        return jsonify({"error": "No subject selected"}), 400
        
    db = get_db()
    current_subject = session['current_subject']
    
    if request.is_json:
        data = request.json
    else:
        data = request.form
    
    teacher_id = data.get('teacher_id')
    date = data.get('date')
    status = data.get('status')
    
    if not all([teacher_id, date, status]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        # Check if the teacher exists in the current subject
        teacher = db.execute('''
            SELECT id FROM teachers 
            WHERE id = ? AND subject = ?
        ''', (teacher_id, current_subject)).fetchone()
        
        if not teacher:
            return jsonify({"error": "Teacher not found in this subject"}), 404
        
        # Check for existing attendance record
        existing_record = db.execute('''
            SELECT id FROM attendance 
            WHERE teacher_id = ? AND date = ? AND subject = ?
        ''', (teacher_id, date, current_subject)).fetchone()
        
        if existing_record:
            # Update existing record
            db.execute('''
                UPDATE attendance 
                SET status = ? 
                WHERE id = ?
            ''', (status, existing_record['id']))
        else:
            # Create new record
            db.execute('''
                INSERT INTO attendance (teacher_id, date, status, subject)
                VALUES (?, ?, ?, ?)
            ''', (teacher_id, date, status, current_subject))
        
        db.commit()
        return jsonify({"success": True, "status": status})
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_attendance_legacy')
def api_get_attendance_legacy():
    """Legacy endpoint for getting attendance records.
    This is kept for backward compatibility."""
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
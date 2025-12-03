import sqlite3
import os

def fix_teacher_schema():
    # Connect to the database
    db_path = 'teacher_attendance.db'
    backup_path = 'teacher_attendance_backup.db'
    
    # Create a backup of the database
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Created backup at: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Create a new teachers table with the correct schema
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            UNIQUE(employee_id, subject)  -- This is the composite key
        )
        ''')
        
        # 2. Copy data from old table to new table
        cursor.execute('''
        INSERT OR IGNORE INTO teachers_new (id, name, department, employee_id, subject)
        SELECT id, name, department, employee_id, COALESCE(subject, 'TCS 302')
        FROM teachers
        ''')
        
        # 3. Drop the old table
        cursor.execute('DROP TABLE IF EXISTS teachers_old')
        
        # 4. Rename tables
        cursor.execute('ALTER TABLE teachers RENAME TO teachers_old')
        cursor.execute('ALTER TABLE teachers_new RENAME TO teachers')
        
        # 5. Update the attendance table to handle the new schema
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            subject TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id) ON DELETE CASCADE,
            UNIQUE(teacher_id, date, subject)
        )
        ''')
        
        # 6. Copy attendance data
        cursor.execute('''
        INSERT INTO attendance_new (id, teacher_id, date, status, note, subject)
        SELECT a.id, a.teacher_id, a.date, a.status, a.note, COALESCE(a.subject, t.subject, 'TCS 302')
        FROM attendance a
        JOIN teachers t ON a.teacher_id = t.id
        ''')
        
        # 7. Drop old attendance table
        cursor.execute('DROP TABLE IF EXISTS attendance_old')
        cursor.execute('ALTER TABLE attendance RENAME TO attendance_old')
        cursor.execute('ALTER TABLE attendance_new RENAME TO attendance')
        
        conn.commit()
        print("Database schema updated successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        if os.path.exists(backup_path):
            print(f"Restoring from backup...")
            shutil.copy2(backup_path, db_path)
            print("Database restored from backup")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting database schema update...")
    fix_teacher_schema()
    print("Process completed. Please restart your application.")
    print("Note: A backup of your database was created as 'teacher_attendance_backup.db' in case you need to restore.")

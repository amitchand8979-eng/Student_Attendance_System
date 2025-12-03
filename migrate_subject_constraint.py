import sqlite3

def migrate_database():
    # Connect to the database
    conn = sqlite3.connect('teacher_attendance.db')
    cursor = conn.cursor()
    
    try:
        # Create a new table with the updated schema
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            UNIQUE(employee_id, subject)
        )
        ''')
        
        # Copy data from old table to new table
        cursor.execute('''
        INSERT INTO teachers_new (id, employee_id, name, subject)
        SELECT id, employee_id, name, COALESCE(subject, 'TCS 302') as subject 
        FROM teachers
        ''')
        
        # Drop the old table
        cursor.execute('DROP TABLE teachers')
        
        # Rename new table to original name
        cursor.execute('ALTER TABLE teachers_new RENAME TO teachers')
        
        # Update the attendance table to include subject in the unique constraint
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            subject TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id),
            UNIQUE(teacher_id, date, subject)
        )
        ''')
        
        # Copy data from old attendance table to new table
        cursor.execute('''
        INSERT INTO attendance_new (id, teacher_id, date, status, subject)
        SELECT a.id, a.teacher_id, a.date, a.status, COALESCE(a.subject, t.subject, 'TCS 302') as subject
        FROM attendance a
        JOIN teachers t ON a.teacher_id = t.id
        ''')
        
        # Drop the old attendance table
        cursor.execute('DROP TABLE attendance')
        
        # Rename new attendance table to original name
        cursor.execute('ALTER TABLE attendance_new RENAME TO attendance')
        
        # Commit changes
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting database migration...")
    migrate_database()
    print("Migration completed. Please restart your application.")

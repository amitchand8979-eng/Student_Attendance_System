import sqlite3

def migrate_database():
    # Connect to the database
    conn = sqlite3.connect('teacher_attendance.db')
    cursor = conn.cursor()
    
    try:
        # Add subject column to teachers table if it doesn't exist
        cursor.execute("PRAGMA table_info(teachers)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'subject' not in columns:
            cursor.execute("ALTER TABLE teachers ADD COLUMN subject TEXT DEFAULT 'TCS 302'")
        
        # Add subject column to attendance table if it doesn't exist
        cursor.execute("PRAGMA table_info(attendance)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'subject' not in columns:
            cursor.execute("ALTER TABLE attendance ADD COLUMN subject TEXT DEFAULT 'TCS 302'")
        
        # Commit changes
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

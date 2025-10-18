# Teacher Attendance System

A Flask web application for managing teacher attendance with MongoDB Atlas as the database.

## Features

- Dashboard with attendance statistics
- Add and manage teachers
- Mark and update attendance
- View and filter attendance records
- RESTful API endpoints

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`

## API Endpoints

- GET `/api/teachers` - Get all teachers
- POST `/api/mark_attendance` - Mark or update attendance
- GET `/api/get_attendance` - Get attendance records with optional filters

## Technologies Used

- Flask
- MongoDB Atlas
- Bootstrap 5
- jQuery
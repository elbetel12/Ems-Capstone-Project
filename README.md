# Employee Management System (Django)

A comprehensive Employee Management System built with Django.

## Features

- User Authentication and Role-Based Access Control
- Employee Management (Add, Update, Delete)
- Department Management
- Attendance Tracking with QR Code
- Leave Management (Request and Approve)
- Payroll System
- Performance Evaluation
- Work Hours Reporting
- Admin Dashboard with Statistics

## Tech Stack

- Django (Python Web Framework)
- SQLite Database
- HTML/CSS/JavaScript
- Bootstrap
- jQuery
- Chart.js for Data Visualization

## Installation

1. Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/django-employee-management.git
cd django-employee-management
```

2. Create a virtual environment and activate it:

```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run migrations:

```bash
python manage.py migrate
```

5. Create a superuser:

```bash
python manage.py createsuperuser
```

6. Run the development server:

```bash
python manage.py runserver
```

7. Access the application at http://127.0.0.1:8000/

## Usage

1. Login with your admin credentials
2. Navigate through the sidebar to access different modules
3. Add departments and employees
4. Manage attendance, leaves, and payroll
5. Generate reports

## License

This project is licensed under the MIT License - see the LICENSE file for details.

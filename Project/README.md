# Equipment Rental System

A Django-based equipment rental management system for leisure equipment. The system allows customers to browse and reserve equipment, staff to manage returns and maintenance, and managers to oversee inventory and categories.

## Features

- User role-based access control (Customer, Staff, Manager, Admin)
- Equipment catalog with category filtering
- Reservation system with date-based availability
- Maintenance scheduling, tracking, and cancellation
- Equipment return processing
- Inventory management
- Report generation
- Staff account management

## Prerequisites

- Python 3.13 or higher
- Django 5.2 or higher
- SQLite3
- Bootstrap 5

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd equipment-rental
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Apply database migrations:
```bash
python manage.py migrate
```

5. Load initial data:
```bash
python manage.py loaddata users/fixtures/users.json
python manage.py loaddata core/fixtures/user_profiles.json
python manage.py loaddata inventory/fixtures/categories.json
python manage.py loaddata inventory/fixtures/items.json
python manage.py loaddata core/fixtures/maintenance.json
```

## Default Users

All users have the password: `password`

- Admin: admin@admin.com
- Customer: user1@user1.com
- Staff: staff@staff.com
- Manager: manager@manager.com

## Running the Application

1. Start the development server:
```bash
python manage.py runserver
```

2. Access the application at: http://127.0.0.1:8000

## Running Tests

To run all tests:
```bash
python manage.py test
```

To run specific test cases:
```bash
python manage.py test core.tests
python manage.py test inventory.tests
python manage.py test users.tests
```

Available test cases:
- core.tests:
  - MaintenanceAndReservationTest
    - test_schedule_maintenance
    - test_reserve_item
    - test_maintenance_blocks_reservation
    - test_cancel_maintenance
- users.tests:
  - UserAuthenticationTest
    - test_user_login
    - test_user_roles
    - test_unauthorized_access
- inventory.tests:
  - InventoryManagementTest
    - test_category_creation
    - test_item_creation
    - test_catalog_view
    - test_inventory_management

## Project Structure

```
equipment_rental/
├── core/                 # Core functionality and maintenance
├── inventory/            # Inventory and category management
├── users/               # User authentication and profiles
├── reservations/        # Reservation system
└── templates/           # HTML templates
```

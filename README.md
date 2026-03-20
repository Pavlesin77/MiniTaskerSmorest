# MiniTaskerSmorest

## Overview

MiniTaskerSmorest is a follow-up experiment to MiniTasker, rebuilt using an object-oriented approach with Flask-Smorest, Marshmallow schemas for validation, and JWT authentication. It introduces role-based access control, soft delete, and a full audit log system that tracks all user actions.

The project served as a direct stepping stone toward more structured and production-ready API design.

## Technologies

- **Backend:** Flask (OOP approach via Flask-Smorest MethodView)
- **Database:** PostgreSQL (local)
- **ORM:** SQLAlchemy + Flask-Migrate
- **Validation:** Marshmallow schemas
- **Authentication:** JWT (Flask-JWT-Extended)
- **API Documentation:** Auto-generated OpenAPI spec via Flask-Smorest

## Architecture

The project is organized into the following layers:

- `app/models/` — SQLAlchemy models (User, Task, AuditLog)
- `app/schemas/` — Marshmallow schemas for request validation and response serialization
- `app/resources/` — Flask-Smorest blueprints and MethodView classes (routes)
- `app/utils/` — Utility functions (audit log creation)
- `app/extensions.py` — Flask extensions (SQLAlchemy, Migrate)

## Features

### Users
- User registration and login (JWT authentication)
- Login via username or email
- View and update own profile (`/users/me`)
- Soft delete (account deactivation, not permanent removal)

### Role-Based Access Control
- **Regular user** — can manage own account
- **Admin** — can view all active users, look up users by username/email
- **Superadmin** — first registered user; can manage admin status, view deactivated accounts, access audit logs

### Tasks
- Full CRUD for tasks
- Tasks are linked to users via foreign key relationship

### Audit Log
- Every significant action is recorded (registration, login, profile update, admin changes)
- Superadmin can query audit logs with filters (actor, target, date range)

## Installation

pip install -r requirements.txt

Configure your database credentials in a `.env` file:

DATABASE_URL=postgresql://your_user:your_password@localhost:5432/minitasker_smorest
JWT_SECRET_KEY=your_jwt_secret

Run database migrations:

flask db upgrade

Start the application:

python manage.py

## API Endpoints

### Users

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/users/register` | Public | Register a new user |
| POST | `/users/login` | Public | Login (returns JWT token) |
| GET | `/users/me` | Authenticated | View own profile |
| PATCH | `/users/me` | Authenticated | Update own profile |
| DELETE | `/users/<id>` | Admin or self | Soft delete user |
| GET | `/users/` | Admin | List all active users |
| GET | `/users/deleted` | Superadmin | List deactivated users |
| GET | `/users/lookup` | Admin | Find user by username or email |
| PATCH | `/users/<id>/make_admin` | Superadmin | Change admin status |
| GET | `/users/audit-logs` | Superadmin | View audit logs |

### Tasks

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/tasks/` | Authenticated | List own tasks |
| POST | `/tasks/` | Authenticated | Create a new task |
| GET | `/tasks/<id>` | Authenticated | Get a single task |
| PATCH | `/tasks/<id>` | Authenticated | Update a task |
| DELETE | `/tasks/<id>` | Delete a task |

## Comparison with MiniTasker

| Feature | MiniTasker | MiniTaskerSmorest |
|--------|------------|-------------------|
| Approach | Functional | OOP (MethodView) |
| Validation | Manual (if checks) | Marshmallow schemas |
| Authentication | Sessions | JWT |
| Role system | No | Yes (user/admin/superadmin) |
| Audit log | No | Yes |
| Soft delete | No | Yes |
| OpenAPI docs | No | Yes (auto-generated) |


# Pool Time Scheduler API

Backend API for managing swimming pool schedules, instructors, and visitors built with FastAPI.

## Features

- **Role-based access control** (Administrator, Instructor, Visitor)
- **Group management** with capacity constraints
- **Instructor scheduling** with hour limits and preferences
- **Visitor registrations** with gender-specific capacity limits
- **REST API** with Swagger documentation

## Requirements

- Python 3.8+
- PostgreSQL

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure PostgreSQL connection in `app/core/config.py`
4. Create tables and seed test data:
   ```
   python -m scripts.seed_data
   ```
5. Run the application:
   ```
   python run.py
   ```

## Docker Setup

The application can be run using Docker and docker-compose:

```
docker-compose up -d
```

This will start both the PostgreSQL database and the API server.

## API Documentation

After starting the application, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Default Users

The seed script creates the following users:

- **Admin**: 
  - Email: admin@example.com
  - Password: admin123

- **Instructors**:
  - Email: instructor1@example.com (through instructor5@example.com)
  - Password: instructor1 (through instructor5)

- **Visitors**:
  - Email: visitor1@example.com (through visitor20@example.com)
  - Password: visitor1 (through visitor20)

## API Endpoints

The API provides endpoints for:

- User management and authentication
- Group creation and management
- Instructor availability and preferences
- Visitor registrations
- Attendance tracking

For a complete list of endpoints, refer to the Swagger documentation.

## Testing

Basic tests can be run with:

```
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

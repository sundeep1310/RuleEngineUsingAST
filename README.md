# Rule Engine Application

## Overview

This Rule Engine Application is a web-based tool that allows users to create, manage, and evaluate rules based on given data. It provides a simple interface for defining complex logical rules and testing them against JSON data.

## Features

- User authentication (login and registration)
- Create new rules using a simple syntax
- View all existing rules
- Delete individual rules
- Delete all rules at once
- Evaluate data against the created rules
- RESTful API for rule management and evaluation

## Technology Stack

- Backend: Flask (Python)
- Frontend: HTML, JavaScript, Tailwind CSS
- Database: SQLite (configurable to other databases)
- Additional libraries: Flask-CORS, Flask-Limiter, Flask-SQLAlchemy, Flask-Caching, Flask-Login

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd rule-engine-application
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add the following variables:
   ```
   SECRET_KEY=your_secret_key
   DATABASE_URL=sqlite:///rules.db
   ```

5. Initialize the database:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. Run the application:
   ```
   python app.py
   ```

The application should now be running on `http://localhost:5000`.

## Usage

### User Authentication

- Register a new account using the registration page.
- Log in using your credentials on the login page.

### Creating Rules

Rules should be entered in the following format:
```
(attribute operator value) AND/OR (attribute operator value)
```

Operators: `=`, `>`, `<`

Example:
```
(age > 30 AND department = 'Sales') OR (salary < 50000)
```

### Evaluating Rules

Enter JSON data matching the attributes in your rules. For example:
```json
{"age": 35, "department": "Sales", "salary": 60000}
```

### API Endpoints

- `POST /api/create_rule`: Create a new rule
- `POST /api/evaluate_rule`: Evaluate data against existing rules
- `GET /api/get_rules`: Retrieve all existing rules
- `DELETE /api/delete_rule/<rule_id>`: Delete a specific rule
- `DELETE /api/delete_all_rules`: Delete all rules

Note: All API endpoints require user authentication.

## Security

- User passwords are hashed before storing in the database.
- Rate limiting is implemented to prevent abuse of the API.
- CORS is configured to control which domains can access the API.

## Caching

The application uses Flask-Caching to improve performance by caching frequent database queries and API responses.

## Troubleshooting

### rules.db Error

If you encounter an error related to `rules.db`, follow these steps:

1. Stop the application if it's running.

2. Delete the existing `rules.db` file:
   ```
   rm instance/rules.db
   ```
   Note: The path might be different depending on your project structure. Adjust accordingly.

3. Reinitialize the database:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

4. Restart your application:
   ```
   python app.py
   ```

This process will create a fresh `rules.db` file and should resolve any issues related to database schema mismatches or corrupted database files.

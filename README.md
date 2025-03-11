# RevoBank API

A RESTful API for RevoBank, implementing core banking features including User Management, Account Management, and Transaction Management.

## Features

- User Management (registration, authentication, profile management)
- Account Management (create, view, update, delete bank accounts)
- Transaction Management (deposits, withdrawals, transfers)
- JWT-based authentication
- PostgreSQL database integration
- Docker containerization

## Installation and Setup

### Prerequisites

- Docker and Docker Compose
- Git

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd milestone-3-atfdeenk-module-7
   ```

2. Configure environment variables:
   Create a `.env` file in the root directory:
   ```env
   FLASK_APP=app.py
   FLASK_ENV=development
   DATABASE_URL=postgresql://revobank:revobank@db:5432/revobank
   SECRET_KEY=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret-key
   ```

3. Start the application:
   ```bash
   docker-compose up --build
   ```

### Testing

You can test the API using tools like APIdog, Postman, or curl. Example curl commands:

1. Create a user:
   ```bash
   curl -X POST http://localhost:5001/users \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"secure123","name":"John Doe"}'
   ```

2. Login:
   ```bash
   curl -X POST http://localhost:5001/users/login \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"secure123"}'
   ```

3. Create an account (with token):
   ```bash
   curl -X POST http://localhost:5001/accounts \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-token" \
     -d '{"account_type":"savings"}'
   ```

The API will be available at `http://localhost:5001`

## API Documentation

### Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your-token>
```

### User Management

#### Create User
- **POST** `/users`
- Body:
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password",
    "name": "John Doe"
  }
  ```

#### Login
- **POST** `/users/login`
- Body:
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password"
  }
  ```

#### Get User Profile
- **GET** `/users/me`
- Protected: Yes

#### Update User Profile
- **PUT** `/users/me`
- Protected: Yes
- Body:
  ```json
  {
    "name": "New Name",
    "email": "newemail@example.com"
  }
  ```

### Account Management

#### List Accounts
- **GET** `/accounts`
- Protected: Yes

#### Get Account Details
- **GET** `/accounts/:id`
- Protected: Yes

#### Create Account
- **POST** `/accounts`
- Protected: Yes
- Body:
  ```json
  {
    "account_type": "savings"
  }
  ```

#### Update Account
- **PUT** `/accounts/:id`
- Protected: Yes
- Body:
  ```json
  {
    "account_type": "checking"
  }
  ```

#### Delete Account
- **DELETE** `/accounts/:id`
- Protected: Yes

### Transaction Management

#### List Transactions
- **GET** `/transactions`
- Protected: Yes
- Query Parameters:
  - `account_id` (optional)
  - `start_date` (optional, ISO format)
  - `end_date` (optional, ISO format)

#### Get Transaction Details
- **GET** `/transactions/:id`
- Protected: Yes

#### Create Transaction
- **POST** `/transactions`
- Protected: Yes
- Body for Transfer:
  ```json
  {
    "transaction_type": "transfer",
    "amount": 100.00,
    "from_account_id": 1,
    "to_account_id": 2,
    "description": "Transfer to savings"
  }
  ```
- Body for Deposit/Withdrawal:
  ```json
  {
    "transaction_type": "deposit",
    "amount": 100.00,
    "account_id": 1,
    "description": "Initial deposit"
  }
  ```

## Docker Commands

- Start application: `docker-compose up --build`
- Run in background: `docker-compose up -d`
- View logs: `docker-compose logs`
- Stop application: `docker-compose down`
- Stop and remove volumes: `docker-compose down -v`

## Database

The application uses PostgreSQL as its database. The database is automatically created and configured when you start the application using Docker Compose.

## Deployment

The API is deployed on Render and can be accessed at: [RevoBank API](https://revobank-api.onrender.com)

### Deployment Instructions

1. Fork or clone this repository to your GitHub account

2. Create a new Web Service on Render:
   - Connect your GitHub repository
   - Choose the Python environment
   - Set the following environment variables:
     ```
     FLASK_APP=app.py
     FLASK_ENV=production
     SECRET_KEY=<your-secret-key>
     JWT_SECRET_KEY=<your-jwt-secret-key>
     ```
   - The database URL will be automatically configured by Render

3. Deploy:
   - Render will automatically deploy your application
   - Any new commits to the main branch will trigger automatic deployments

### Production Considerations

- The API uses gunicorn as the production WSGI server
- Database migrations will run automatically during deployment
- CORS is configured to allow requests from specified origins
- All sensitive data is stored in environment variables

Default credentials (for development):
- Database: revobank
- Username: revobank
- Password: revobank
- Host: localhost
- Port: 5432

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages in JSON format:

- 400: Bad Request (invalid input)
- 401: Unauthorized (missing or invalid token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 409: Conflict (e.g., duplicate email)
- 422: Unprocessable Entity
- 500: Internal Server Error

Example error response:
```json
{
  "error": "Detailed error message"
}
```

## Database Schema

### User
- id: Primary key
- email: Unique email address
- password_hash: Securely hashed password
- name: User's name
- created_at: Account creation timestamp

### Account
- id: Primary key
- account_number: Unique account identifier
- account_type: Type of account (checking, savings)
- balance: Current balance
- created_at: Account creation timestamp
- user_id: Foreign key to User

### Transaction
- id: Primary key
- transaction_type: Type (deposit, withdrawal, transfer)
- amount: Transaction amount
- from_account_id: Source account (Foreign key)
- to_account_id: Destination account (Foreign key)
- timestamp: Transaction timestamp
- status: Transaction status
- description: Optional description

## Security Notes

1. Change the default database credentials in production
2. Update the SECRET_KEY and JWT_SECRET_KEY environment variables
3. Enable HTTPS in production
4. Implement rate limiting for production use
5. Passwords are hashed using pbkdf2_sha256
6. All timestamps are stored in UTC
7. Database transactions ensure data consistency

## Data Validation

### User Input Validation
- Email must be a valid email format
- Password must be at least 6 characters
- Name cannot be empty
- All string inputs are trimmed of whitespace

### Transaction Validation
- Amount must be positive
- Account must have sufficient balance for withdrawals/transfers
- Account ownership is verified for all operations
- Transaction types must be: deposit, withdrawal, or transfer

### Account Validation
- Account types must be: checking or savings
- Account numbers are automatically generated
- One user can have multiple accounts
- Account balance cannot be negative
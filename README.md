# TaskMaster Backend API

A robust, scalable backend API for the TaskMaster application, built with **FastAPI**.

## 🚀 Key Features

- **High Performance:** Built on FastAPI (ASGI) for speed.
- **Authentication:** JWT-based auth with access/refresh token rotation.
- **Role-Based Access Control (RBAC):** Admin and User roles.
- **Advanced Task Management:** CRUD, filtering, pagination, and optimistic locking.
- **API Versioning:** Support for v1 and v2 APIs.
- **Security:** Rate limiting, secure password hashing, and CORS protection.
- **Database:** SQLAlchemy ORM with SQLite (dev) / PostgreSQL (prod ready).
- **Password Reset:** OTP-based secure password recovery via email.

## 🛠️ Tech Stack

- **Framework:** FastAPI
- **Language:** Python 3.10+
- **Database:** SQLite (default) / SQLAlchemy
- **Authentication:** Python-Jose (JWT), Passlib (Bcrypt)
- **Validation:** Pydantic
- **Email:** Aiosmtplib
- **Testing:** Pytest

## 📋 Prerequisites

- Python 3.10 or higher
- Redis (optional, for caching/rate limiting in production)

## ⚡ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Update `.env` with your settings (especially Email config for password reset):
     ```ini
     SMTP_HOST=smtp.gmail.com
     SMTP_PORT=587
     SMTP_USER=your-email@gmail.com
     SMTP_PASSWORD=your-app-password
     ```

5. **Run Migrations (if using Alembic):**
   ```bash
   alembic upgrade head
   ```
   *Note: For this assignment, tables are auto-created on startup if they don't exist.*

## 🏃‍♂️ Running the Server

Start the development server with hot-reload:

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

## 📚 API Documentation

### Interactive Docs
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### 🔑 Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/register` | Register a new user | Public |
| `POST` | `/login` | Login and get tokens | Public |
| `POST` | `/refresh` | Refresh access token | Public |
| `POST` | `/logout` | Logout (blacklist token) | Authenticated |
| `GET` | `/me` | Get current user profile | Authenticated |

### 🔐 Password Reset (`/api/v1/auth`)

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/forgot-password` | Request 6-digit OTP via email | Public |
| `POST` | `/verify-reset-token` | Verify if a token is valid | Public |
| `POST` | `/reset-password` | Reset password using OTP | Public |

### 👤 Users (`/api/v1/users`)

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | List all users | Admin |
| `GET` | `/{id}` | Get specific user details | Admin/Self |
| `PATCH` | `/{id}/role` | Update user role | Admin |

### ✅ Tasks V1 (`/api/v1/tasks`)

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | List tasks (pagination/filtering) | Authenticated |
| `POST` | `/` | Create a new task | Authenticated |
| `GET` | `/{id}` | Get task details | Authenticated |
| `PUT` | `/{id}` | Update task (optimistic lock) | Authenticated |
| `DELETE` | `/{id}` | Delete task | Authenticated |

### ✅ Tasks V2 (`/api/v2/tasks`)

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | List tasks (advanced filtering) | Authenticated |

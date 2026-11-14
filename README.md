# SkillBridge – Career Readiness and Skill Development Platform

SkillBridge is a web-based platform designed to help students improve their technical skills and prepare for career opportunities through assessments, coding challenges, and performance tracking.

The platform provides separate interfaces for students and teachers, making it easier to conduct assessments and monitor learning progress.

## Project Status

**Currently in Development (In Progress)**

This project is being developed as a third-year engineering major project.

## Key Features

### Student Module
- Student registration and login
- Access to assigned assessments
- Attempt MCQ-based questions
- Solve programming challenges
- View assessment results

### Teacher Module
- Teacher authentication
- Create and manage assessments
- Add MCQ and coding questions
- Add test cases for coding questions
- View student assessment results

### Additional Features
- AI-assisted question generation
- Online code execution using Judge0
- Exam security and warning mechanism
- Role-based access for students and teachers

## Technology Stack

**Backend**
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT Authentication

**Frontend**
- React
- Vite
- JavaScript
- CSS
- Axios
- React Router

**Other Tools**
- Git and GitHub
- Judge0
- AI integration

## Project Structure

```text
SkillBridge/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── Auth.jsx
│   │   └── api.js
│   └── package.json
├── routers/
├── services/
├── main.py
├── models.py
├── schemas.py
├── database.py
├── ai_service.py
├── judge0_service.py
└── .gitignore
```

## Running the Project Locally

### 1. Clone the Repository

```bash
git clone https://github.com/riyagautam-dev/SkillBridge.git
cd SkillBridge
```

### 2. Backend Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Install the backend dependencies required by the project.

Create a `.env` file in the root directory and configure your database connection, JWT secret, and required API keys.

Start the backend:

```bash
python -m uvicorn main:app --reload
```

Backend API documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend in your browser:

```text
http://localhost:5173
```

## Future Enhancements

- Complete student and teacher dashboard integration
- Advanced student performance analytics
- Improved assessment monitoring
- Additional career-readiness features
- Further UI/UX improvements

## Author

**SkillBridge – Engineering Major Project**

GitHub Repository: https://github.com/riyagautam-dev/SkillBridge

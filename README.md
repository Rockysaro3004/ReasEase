# ReadEase – Smart Reading Assistant for Students

> **Tagline:** *Read Smarter. Understand Better. Learn Faster.*  
> **Project Type:** Full-Stack Educational Web Application (Python Internship Mini-Project)

---

## 1. Project Overview

**ReadEase** is a full-stack educational web application engineered specifically for college and school students who face cognitive overload from dense academic textbooks, research papers, and lecture materials. 

Many students struggle with:
- Lengthy, unstructured PDFs with distracting layouts and broken formatting.
- Complex academic and technical vocabulary without immediate contextual explanations.
- Auditory learning preferences where reading on screens causes visual fatigue.
- Ineffective passive reading without active recall or comprehension self-testing.

**ReadEase solves this** by extracting clean text from uploaded PDF materials and providing four integrated reading enhancement tools:
1. **Extractive Text Summarization:** Algorithmic sentence scoring to condense long chapters into high-salience summaries (Short ~20%, Medium ~35%, Long ~50%).
2. **Academic Vocabulary Assistant:** Automatic identification of collegiate terminology with verified meanings, examples, and a personal saved notebook.
3. **Web Speech Audio Narration:** Browser-native speech synthesis with play, pause, resume, stop, and rate adjustments.
4. **Active Recall Quiz Generator:** Grounded multiple-choice questions extracted directly from source statements with verifiable answers.

---

## 2. Technology Stack

| Layer | Technologies Used |
|---|---|
| **Frontend** | HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, JavaScript (ES6+), Jinja2 Templates |
| **Backend** | Python 3.10+, Flask 3.0, Flask-WTF (CSRF & Form Validation), Flask-Login |
| **Database & ORM** | SQLite 3, SQLAlchemy (Flask-SQLAlchemy) |
| **PDF Processing** | PyMuPDF (`fitz`) for fast and robust local text extraction |
| **Text Processing** | Custom Python Frequency Scoring & Lexical Analysis (Zero heavy downloads) |
| **Text-to-Speech** | Browser Web Speech API (`SpeechSynthesis`) |
| **Data Visualization**| Chart.js (Dashboard study analytics) |
| **Security** | PBKDF2/SHA-256 Password Hashing, Timed ItsDangerous Reset Tokens, User Scoping |

---

## 3. System Architecture & Communication Flow

ReadEase follows a modular Model-View-Controller (MVC) architectural pattern:

```
[ Client Browser (Chrome / Edge / Firefox) ]
      │
      │ HTTP Requests (Forms, File Uploads, Navigation)
      ▼
[ Flask Application Factory & Blueprints ]
   ├── auth_bp      (/auth/login, /auth/register, /auth/forgot-password)
   ├── main_bp      (/, /dashboard, /profile)
   └── documents_bp (/documents, /documents/upload, /summary, /quiz, /tts)
      │
      ├─── Service Layer (Isolated Business Logic)
      │     ├── PDFProcessor     (PyMuPDF text extraction)
      │     ├── Summarizer       (Sentence frequency scoring)
      │     ├── Vocabulary       (Curated academic lexicon & API fallback)
      │     └── QuizGenerator    (Rule-based definition & Cloze questions)
      │
      └─── Data Layer (Flask-SQLAlchemy ORM)
            ├── User Model        (Authentication & Relationships)
            ├── Document Model    (Metadata & Extracted Text)
            ├── Summary Model     (Extracted Summaries)
            ├── Vocabulary Model  (Saved Notebook Items)
            └── QuizResult Model  (Scoring Records)
                  │
                  ▼
         [ SQLite Database (instance/readease.db) ]
```

### Communication Flow:
1. **Frontend to Backend:** Forms submit via HTTP POST with CSRF tokens (`Flask-WTF`). The browser requests pages rendered dynamically by Jinja2 templates.
2. **Backend to Database:** Controllers query the SQLite database via SQLAlchemy ORM, ensuring **every query is filtered by `current_user.id`** so students can only access their own files.
3. **Audio Playback:** The text-to-speech engine operates locally on the client machine via the browser's native `window.speechSynthesis` API, requiring zero expensive external audio cloud APIs.

---

## 4. Database Schema

The application uses an SQLite relational database (`instance/readease.db`):

- **`users` Table:**
  - `id` (INTEGER, Primary Key)
  - `full_name` (VARCHAR(120), Not Null)
  - `email` (VARCHAR(120), Unique, Indexed)
  - `password_hash` (VARCHAR(255), Not Null)
  - `is_verified` (BOOLEAN, Default False)
  - `created_at` (DATETIME, UTC Timestamp)

- **`documents` Table:**
  - `id` (INTEGER, Primary Key)
  - `user_id` (INTEGER, Foreign Key -> `users.id` on delete CASCADE)
  - `original_filename` (VARCHAR(255), Not Null)
  - `stored_filename` (VARCHAR(255), Unique)
  - `extracted_text` (TEXT, Not Null)
  - `upload_date` (DATETIME, UTC Timestamp)

- **`summaries` Table:**
  - `id` (INTEGER, Primary Key)
  - `document_id` (INTEGER, Foreign Key -> `documents.id` on delete CASCADE)
  - `user_id` (INTEGER, Foreign Key -> `users.id` on delete CASCADE)
  - `summary_text` (TEXT, Not Null)
  - `summary_length` (VARCHAR(50), e.g. 'short', 'medium', 'long')
  - `created_at` (DATETIME, UTC Timestamp)

- **`vocabulary` Table:**
  - `id` (INTEGER, Primary Key)
  - `user_id` (INTEGER, Foreign Key -> `users.id` on delete CASCADE)
  - `document_id` (INTEGER, Foreign Key -> `documents.id`, Nullable)
  - `word` (VARCHAR(100), Not Null)
  - `meaning` (TEXT, Nullable)
  - `created_at` (DATETIME, UTC Timestamp)

- **`quiz_results` Table:**
  - `id` (INTEGER, Primary Key)
  - `user_id` (INTEGER, Foreign Key -> `users.id` on delete CASCADE)
  - `document_id` (INTEGER, Foreign Key -> `documents.id` on delete CASCADE)
  - `score` (INTEGER, Not Null)
  - `total_questions` (INTEGER, Not Null)
  - `completed_at` (DATETIME, UTC Timestamp)

---

## 5. Step-by-Step Installation & Setup (Windows Command Prompt)

Follow these exact steps to set up and run ReadEase on a Windows laptop.

### Step 1: Verify Python Installation
Open **Command Prompt** (`cmd.exe`) and check:
```cmd
python --version
```
*(If Python is not installed, download Python 3.10+ from python.org and ensure "Add Python to PATH" is checked during installation).*

### Step 2: Navigate to Project Folder
```cmd
cd C:\path\to\ReadEase
```

### Step 3: Create a Python Virtual Environment
Creating a virtual environment isolates project dependencies:
```cmd
python -m venv venv
```

### Step 4: Activate the Virtual Environment
```cmd
venv\Scripts\activate
```
*(You will see `(venv)` appear at the start of your command prompt).*

### Step 5: Install Dependencies
```cmd
pip install -r requirements.txt
```

### Step 6: Configure Environment Variables
Copy `.env.example` to `.env`:
```cmd
copy .env.example .env
```
*(You can leave the default values for local development. SQLite and local safe development mode will work immediately without SMTP).*

### Step 7: Run the Application
```cmd
python run.py
```

### Step 8: Open in Browser
Open your browser (Google Chrome, Microsoft Edge, or Mozilla Firefox) and navigate to:
```
http://127.0.0.1:5000
```

---

## 6. How to Run Automated Unit Tests

ReadEase comes with automated unit tests to verify the core algorithms and database models:

```cmd
python -m unittest tests/test_services.py
python -m unittest tests/test_auth_and_models.py
```

Or run all tests in one command:
```cmd
python -m unittest discover tests
```

---

## 7. Security Features

1. **Password Hashing:** Passwords are never saved in plain text. Stored passwords use Werkzeug's PBKDF2/SHA-256 implementation with unique salt.
2. **CSRF Protection:** All forms include cryptographic CSRF tokens managed by Flask-WTF.
3. **Session Security:** Flask-Login session cookies with strict user isolation.
4. **File Safety:** Uploaded filenames are sanitized with `secure_filename()` and prepended with unique 12-character UUID hashes to prevent filename collisions and path traversal attacks.
5. **Data Isolation:** Every database select, delete, or update query validates that `resource.user_id == current_user.id`. Unauthorized attempts to access another user's document return `403 Forbidden`.
6. **Safe Development Password Reset:** If SMTP email settings are omitted in `.env`, ReadEase generates a secure timed token and displays the reset link directly on screen in development mode with a clear disclaimer, ensuring emails are never falsely claimed to be sent.

---

## 8. Known Limitations

- **Scanned Photo PDFs:** Version 1.0 utilizes PyMuPDF for native digital text extraction. It does not include an OCR (Optical Character Recognition) engine like Tesseract. Scanned picture PDFs without embedded text layers will display an informative message to the user.
- **Web Speech Voice Availability:** The variety and naturalness of text-to-speech voices depend on the operating system and client browser. Chrome and Edge offer high-quality pre-installed natural voices.

---

## 9. Internship Mentor Demonstration Guide

When demonstrating ReadEase to your internship mentor, follow this 5-minute walkthrough:

1. **Landing Page:** Show the clean SaaS design, tagline, and feature cards explaining student benefits.
2. **Registration & Auth:** Register a test student account (e.g. `alex@university.edu`). Highlight password validation and secure hashing.
3. **Dashboard:** Point out the personalized welcome banner, dynamic metric counters (Documents, Summaries, Vocab, Quizzes), and the Chart.js visual breakdown.
4. **PDF Upload & Text Extraction:** Upload a sample chapter PDF. Show how PyMuPDF immediately parses pages into clean text and displays word count and estimated reading time.
5. **Extractive Summary:** Generate a "Medium" summary. Show the side-by-side view, word reduction percentage (e.g. 65% reduction), and explain the sentence-scoring algorithm.
6. **Vocabulary Assistant:** Highlight the extracted academic words, definitions, and click "Save to Notebook". Visit the saved vocabulary notebook.
7. **Audio Reader:** Click "Read Aloud" to demonstrate Web Speech API narration and adjust the speed rate to 1.25x.
8. **Active Recall Quiz:** Open the Quiz tab. Show the grounded questions with 4 choices, select answers, submit, and display the final score along with verified source explanations.
9. **Code Structure:** Open VS Code and walk through the clean Blueprint folder structure (`auth`, `main`, `documents`, `services`).

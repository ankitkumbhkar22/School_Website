# School Website Project

A comprehensive school website application built with Flask and SQLite. This project serves as a complete digital presence for "Friends Public H.S. School," featuring public-facing informational pages and a robust administrative backend.

## Features

### Public Portal
- **Home:** Dynamic homepage featuring notices, upcoming events, and a popup banner slider.
- **About/Academics:** Detailed information about the school's heritage and academic programs.
- **Gallery:** Categorized photo gallery (Grand Events, Achievements, Students Life, Special Day).
- **Faculty:** Faculty directory showcasing the teaching staff and administration.
- **Admissions/Contact:** Inquiry forms for prospective students and parents.
- **Chatbot:** Integrated NLP-based chatbot to assist visitors with common questions (Admissions, etc.).

### Admin Dashboard
- **Authentication:** Secure login for administrators.
- **Notices Management:** Add, edit, and delete school notices.
- **Gallery Management:** Upload and organize gallery images.
- **Faculty Management:** Manage staff profiles and details.
- **Admissions Dashboard:** View and handle incoming admission and contact inquiries.
- **Popup Banners:** Upload and toggle status of interactive promotional popups on the homepage.
- **Principal Message:** Rich text editor for updating the principal's message directly on the site.

## Technology Stack
- **Backend:** Python, Flask
- **Database:** SQLite (managed via `sqlite3`)
- **Frontend:** HTML, CSS, JavaScript (incorporating modern UI/UX principles, animations, and toast notifications)

## Setup & Installation

1. **Clone the repository** (if applicable) or navigate to the project directory.
2. **Create a Python Virtual Environment**:
   ```bash
   python -m venv venv
   ```
3. **Activate the Virtual Environment**:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the Application**:
   ```bash
   flask run
   ```
   Or run the Python file directly:
   ```bash
   python app.py
   ```

## Configuration

Environment variables can be set for:
- `FLASK_SECRET_KEY`: Custom secret key for session management (defaults to "dev-change-me").
- `ADMIN_USERNAME`: Admin panel login username (defaults to "admin").
- `ADMIN_PASSWORD`: Admin panel login password (defaults to "password").

The SQLite database (`school.db`) and necessary upload directories are created automatically upon running the application for the first time.

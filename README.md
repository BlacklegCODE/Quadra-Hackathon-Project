# Skill Gap Analyzer

Compare your skills with a job role. See your readiness score, a priority-ranked gap list, a learning roadmap, project ideas, and progress over time.

**Stack:** Python + FastAPI (backend), SQLite (database, no install needed), React (web page, loaded from a CDN, no Node.js needed).

## Run it (3 steps)

You only need Python 3.10 or newer.

**1. Open a terminal in the project folder, then go into `backend`:**

```bash
cd backend
```

**2. Create a virtual environment and install packages.**

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**3. Start the app:**

```bash
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

The database file `skillgap.db` is created automatically in the `backend` folder the first time you run the app. Data is seeded on first start.

## Using VS Code

1. **File → Open Folder** and choose `skill-gap-analyzer`.
2. Open a terminal (**Terminal → New Terminal**) and run the three steps above.
3. If VS Code asks for a Python interpreter, choose `backend/.venv`.

## Using the app

1. Enter your name and pick a target role, then click **Create profile**.
2. Open **My skills**, set the sliders, and click **Save skills**. Each save records a progress snapshot.
3. Check **Readiness**, **Roadmap**, and **Progress**.

## How the numbers work

- Each role lists skills with a required level (1 to 5) and an importance weight (1 to 5).
- **Gap** = required level minus your level (never below 0).
- **Priority** = gap × importance. Missing skills are ranked by this.
- **Readiness** = sum of (your level capped at required × importance) ÷ sum of (required × importance), as a percentage.
- **Roadmap** groups ranked gaps into phases of three skills, four weeks each. Time estimate: 2 weeks per missing level.
- **Projects** are recommended when they cover at least one missing skill. More covered gaps rank higher.

## Project layout

```
skill-gap-analyzer/
  README.md
  backend/
    requirements.txt
    static/index.html        the whole web page (React)
    app/
      main.py                API routes and page serving
      database.py            SQLite setup (PostgreSQL optional)
      models.py              database tables
      schemas.py             request formats
      seed.py                skills, roles, projects
      services/gap.py        gap, readiness, priority, roadmap logic
```

## API

Interactive docs: http://localhost:8000/docs

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/roles` | List roles |
| GET | `/api/skills` | List skills and learning resources |
| GET / POST | `/api/students` | List or create profiles |
| PATCH | `/api/students/{id}` | Change name or target role |
| GET / PUT | `/api/students/{id}/skills` | Read or save skill levels |
| GET | `/api/students/{id}/analysis` | Readiness, gaps, roadmap, projects |
| GET | `/api/students/{id}/progress` | Readiness history |

## Optional: use PostgreSQL instead of SQLite

Install PostgreSQL, create a database named `skillgap`, then run `pip install psycopg2-binary` and set the connection string before starting:

Windows (PowerShell): `$env:DATABASE_URL="postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/skillgap"`

macOS / Linux: `export DATABASE_URL="postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/skillgap"`

## Troubleshooting

- **"Could not reach the app server"**: the uvicorn command isn't running, or you're on a different port.
- **Page loads but styles or React are missing**: the page loads React from the internet (unpkg.com and Google Fonts), so you need an internet connection the first time.
- **Want a fresh start**: stop the server and delete `backend/skillgap.db`. It is recreated on next start.
- **`python` not found on Windows**: reinstall Python and tick "Add to PATH", or use `py` instead of `python`.

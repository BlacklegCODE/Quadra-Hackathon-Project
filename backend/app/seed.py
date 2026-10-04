from sqlalchemy import func, select

from .models import Project, Role, RoleRequirement, Skill

# (name, category, learning resource)
SKILLS = [
    ("Python", "Programming", "Automate the Boring Stuff with Python (free online book). Then solve 20 small scripts that read and write files."),
    ("JavaScript", "Programming", "javascript.info, from 'The JavaScript language' through 'Promises and async'."),
    ("SQL", "Data", "Mode SQL tutorial, then 30 problems in LeetCode's Database section."),
    ("PostgreSQL", "Data", "Run Postgres in Docker and load a public CSV. Practice indexes and EXPLAIN ANALYZE."),
    ("Pandas", "Data", "Pandas 'Getting started' guide. Clean one messy Kaggle dataset end to end."),
    ("Power BI", "Visualization", "Microsoft Learn Power BI path. Build one dashboard from your own dataset."),
    ("Statistics", "Math", "StatQuest on YouTube: mean, variance, distributions, hypothesis testing."),
    ("Data Modeling", "Data", "Kimball star schema basics. Design fact and dimension tables for a sales dataset."),
    ("ETL Pipelines", "Data Engineering", "Extract a CSV, transform with pandas, load into Postgres. Then automate it."),
    ("dbt", "Analytics Engineering", "dbt Learn free courses. Build staging and marts models on a public dataset."),
    ("Apache Airflow", "Data Engineering", "Airflow quickstart. Convert your ETL script into a DAG with three tasks."),
    ("Apache Spark", "Data Engineering", "PySpark tutorial in the Spark docs. Process a dataset larger than 500 MB."),
    ("Git & GitHub", "Tooling", "Pro Git book chapters 1 to 3. Push every project with clear commit messages."),
    ("Docker", "Tooling", "Docker 'Get started' guide. Containerize one of your Python apps."),
    ("Linux & Shell", "Tooling", "OverTheWire Bandit wargame, levels 0 to 15."),
    ("Cloud Basics", "Cloud", "AWS Cloud Practitioner Essentials (free digital course). Deploy one static page."),
    ("REST API Design", "Backend", "Design five endpoints for a library app. Follow resource naming and status codes."),
    ("FastAPI", "Backend", "FastAPI official tutorial. Build a CRUD API backed by a database."),
    ("React", "Frontend", "react.dev Learn section. Build a small app with state and props."),
    ("Data Structures & Algorithms", "CS Fundamentals", "NeetCode 150 roadmap. Solve two problems a day in Python."),
    ("Communication", "Soft Skills", "Write a one-page case study for every project: problem, approach, result."),
]

# title -> (description, {skill: (required_level 1-5, importance 1-5)})
ROLES = {
    "Data Analyst": (
        "Turns data into decisions with SQL, spreadsheets, and dashboards.",
        {
            "SQL": (4, 5), "Python": (3, 4), "Pandas": (3, 4), "Power BI": (4, 5),
            "Statistics": (3, 4), "Data Modeling": (2, 3), "PostgreSQL": (2, 2),
            "Git & GitHub": (2, 2), "Communication": (4, 4),
        },
    ),
    "Analytics Engineer": (
        "Builds clean, tested data models that analysts can trust.",
        {
            "SQL": (5, 5), "dbt": (4, 5), "Data Modeling": (4, 5), "PostgreSQL": (3, 3),
            "Git & GitHub": (3, 4), "Python": (3, 3), "Pandas": (2, 2), "Power BI": (2, 3),
            "Communication": (3, 3),
        },
    ),
    "Data Engineer": (
        "Moves and transforms data reliably at scale.",
        {
            "Python": (4, 5), "SQL": (4, 5), "PostgreSQL": (3, 4), "ETL Pipelines": (4, 5),
            "Apache Airflow": (3, 4), "Apache Spark": (3, 3), "Docker": (3, 3),
            "Git & GitHub": (3, 3), "Cloud Basics": (3, 4), "Linux & Shell": (3, 3),
            "Data Modeling": (3, 3), "Data Structures & Algorithms": (3, 3),
        },
    ),
    "Backend Developer (Python)": (
        "Builds the APIs and services that power applications.",
        {
            "Python": (5, 5), "FastAPI": (4, 4), "REST API Design": (4, 5),
            "PostgreSQL": (4, 4), "Git & GitHub": (4, 4), "Docker": (3, 3),
            "Linux & Shell": (3, 3), "Data Structures & Algorithms": (3, 4), "Cloud Basics": (2, 2),
        },
    ),
    "Frontend Developer (React)": (
        "Builds the interfaces users see and touch.",
        {
            "JavaScript": (5, 5), "React": (4, 5), "REST API Design": (2, 3),
            "Git & GitHub": (3, 3), "Data Structures & Algorithms": (2, 2), "Communication": (2, 2),
        },
    ),
}

# (title, description, difficulty, [skills])
PROJECTS = [
    ("Student Expense Tracker", "A small app that stores expenses in Postgres and reports monthly totals.", "Easy", ["Python", "SQL", "PostgreSQL", "Git & GitHub"]),
    ("Sales Dashboard", "Model a sales dataset as a star schema and publish a Power BI dashboard with KPI cards.", "Medium", ["Power BI", "SQL", "Data Modeling", "Pandas"]),
    ("City Air Quality Pipeline", "Pull daily AQI readings, clean them with pandas, and load a Postgres warehouse table.", "Medium", ["ETL Pipelines", "Python", "Pandas", "PostgreSQL"]),
    ("Scheduled Pipeline with Airflow", "Run the air-quality pipeline as an Airflow DAG with retries, inside Docker.", "Hard", ["Apache Airflow", "ETL Pipelines", "Docker"]),
    ("dbt Analytics Project", "Build staging and marts layers on a public dataset with tests and docs.", "Medium", ["dbt", "SQL", "Data Modeling", "Git & GitHub"]),
    ("Library Management API", "A FastAPI service with CRUD endpoints, Postgres storage, and a Dockerfile.", "Medium", ["FastAPI", "REST API Design", "PostgreSQL", "Docker"]),
    ("Portfolio Site in React", "A personal site with project pages built from components and JSON data.", "Easy", ["React", "JavaScript", "Git & GitHub"]),
    ("Log Analyzer with Spark", "Parse large server logs with PySpark and report error rates by hour.", "Hard", ["Apache Spark", "Python", "Linux & Shell"]),
    ("Cloud-hosted Dashboard", "Deploy a Streamlit dashboard on a free cloud tier using a Docker image.", "Medium", ["Cloud Basics", "Docker", "Power BI"]),
    ("Algorithm Practice Log", "Solve and document 50 problems by pattern, with time and space notes.", "Easy", ["Data Structures & Algorithms", "Communication"]),
]


def seed_database(db):
    if db.scalar(select(func.count(Skill.id))):
        return

    skills = {}
    for name, category, resource in SKILLS:
        skill = Skill(name=name, category=category, resource=resource)
        db.add(skill)
        skills[name] = skill
    db.flush()

    for title, (description, reqs) in ROLES.items():
        role = Role(title=title, description=description)
        db.add(role)
        db.flush()
        for skill_name, (required, importance) in reqs.items():
            db.add(
                RoleRequirement(
                    role_id=role.id,
                    skill_id=skills[skill_name].id,
                    required_level=required,
                    importance=importance,
                )
            )

    for title, description, difficulty, skill_names in PROJECTS:
        db.add(
            Project(
                title=title,
                description=description,
                difficulty=difficulty,
                skills=[skills[n] for n in skill_names],
            )
        )

    db.commit()

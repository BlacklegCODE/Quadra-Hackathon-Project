import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from . import models
from .database import Base, SessionLocal, engine, get_db
from .quiz_bank import QUESTION_BANK
from .schemas import QuizSubmit, SkillLevelsIn, StudentCreate, StudentUpdate
from .seed import seed_database
from .services.gap import LEVEL_LABELS, analyze_student
from .services.quiz import build_attempt, grade_attempt

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    yield


app = FastAPI(
    title="Skill Gap Analyzer API",
    description="Compare a student's skills with a target role, take quizzes, and get a prioritized roadmap.",
    version="2.0.0",
    lifespan=lifespan,
)


# ---------- helpers ----------

def _get_student(db: Session, student_id: int) -> models.Student:
    student = db.get(models.Student, student_id)
    if not student:
        raise HTTPException(404, "Student not found.")
    return student


def _get_role(db: Session, role_id: int) -> models.Role:
    role = db.get(models.Role, role_id)
    if not role:
        raise HTTPException(404, "Role not found.")
    return role


def _student_out(s: models.Student) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "target_role": {"id": s.target_role.id, "title": s.target_role.title}
        if s.target_role
        else None,
    }


# ---------- system ----------

@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------- reference data ----------

@app.get("/api/skills")
def list_skills(db: Session = Depends(get_db)):
    skills = db.scalars(
        select(models.Skill).order_by(models.Skill.category, models.Skill.name)
    ).all()
    return [
        {"id": s.id, "name": s.name, "category": s.category, "resource": s.resource}
        for s in skills
    ]


@app.get("/api/roles")
def list_roles(db: Session = Depends(get_db)):
    roles = (
        db.scalars(
            select(models.Role)
            .options(joinedload(models.Role.requirements))
            .order_by(models.Role.title)
        )
        .unique()
        .all()
    )
    return [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "skill_count": len(r.requirements),
            "quiz_questions": len(QUESTION_BANK.get(r.title, [])),
        }
        for r in roles
    ]


# ---------- students ----------

@app.get("/api/students")
def list_students(db: Session = Depends(get_db)):
    students = db.scalars(select(models.Student).order_by(models.Student.created_at)).all()
    return [_student_out(s) for s in students]


@app.post("/api/students", status_code=201)
def create_student(body: StudentCreate, db: Session = Depends(get_db)):
    if body.target_role_id is not None:
        _get_role(db, body.target_role_id)
    student = models.Student(name=body.name.strip(), target_role_id=body.target_role_id)
    db.add(student)
    db.commit()
    db.refresh(student)
    return _student_out(student)


@app.get("/api/students/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    return _student_out(_get_student(db, student_id))


@app.patch("/api/students/{student_id}")
def update_student(student_id: int, body: StudentUpdate, db: Session = Depends(get_db)):
    student = _get_student(db, student_id)
    if body.name is not None:
        student.name = body.name.strip()
    if body.target_role_id is not None:
        _get_role(db, body.target_role_id)
        student.target_role_id = body.target_role_id
    db.commit()
    db.refresh(student)
    return _student_out(student)


@app.get("/api/students/{student_id}/skills")
def get_student_skills(student_id: int, db: Session = Depends(get_db)):
    student = _get_student(db, student_id)
    return {"levels": {str(ss.skill_id): ss.level for ss in student.skills}}


@app.put("/api/students/{student_id}/skills")
def save_student_skills(student_id: int, body: SkillLevelsIn, db: Session = Depends(get_db)):
    student = _get_student(db, student_id)
    existing = {ss.skill_id: ss for ss in student.skills}

    for skill_id, level in body.levels.items():
        if not 0 <= level <= 5:
            raise HTTPException(422, f"Level for skill {skill_id} must be between 0 and 5.")
        if not db.get(models.Skill, skill_id):
            raise HTTPException(404, f"Skill {skill_id} does not exist.")
        if skill_id in existing:
            existing[skill_id].level = level
        else:
            student.skills.append(models.StudentSkill(skill_id=skill_id, level=level))

    db.flush()
    readiness = None
    if student.target_role_id:
        readiness = analyze_student(db, student)["readiness"]
        db.add(
            models.ProgressSnapshot(
                student_id=student.id,
                role_id=student.target_role_id,
                readiness=readiness,
            )
        )
    db.commit()
    return {"saved": True, "readiness": readiness}


# ---------- analysis ----------

@app.get("/api/students/{student_id}/analysis")
def student_analysis(student_id: int, db: Session = Depends(get_db)):
    student = _get_student(db, student_id)
    if not student.target_role:
        raise HTTPException(400, "Choose a target role first.")
    return analyze_student(db, student)


@app.get("/api/students/{student_id}/progress")
def student_progress(student_id: int, db: Session = Depends(get_db)):
    _get_student(db, student_id)
    snapshots = db.scalars(
        select(models.ProgressSnapshot)
        .where(models.ProgressSnapshot.student_id == student_id)
        .order_by(models.ProgressSnapshot.created_at, models.ProgressSnapshot.id)
    ).all()
    return [
        {"role_id": s.role_id, "readiness": s.readiness, "created_at": s.created_at.isoformat()}
        for s in snapshots
    ]


# ---------- quiz ----------

@app.get("/api/students/{student_id}/quiz")
def start_quiz(student_id: int, db: Session = Depends(get_db)):
    """Create a new quiz for the student's target role. Questions are shuffled, answers stay hidden."""
    student = _get_student(db, student_id)
    if not student.target_role:
        raise HTTPException(400, "Choose a target role first.")
    role_title = student.target_role.title
    if role_title not in QUESTION_BANK:
        raise HTTPException(404, "No quiz is available for this role yet.")

    items = build_attempt(role_title)
    attempt = models.QuizAttempt(
        student_id=student.id,
        role_id=student.target_role_id,
        payload=json.dumps(items),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "role": role_title,
        "total": len(items),
        "questions": [
            {
                "number": i + 1,
                "skill": it["skill"],
                "question": it["question"],
                "options": it["options"],
            }
            for i, it in enumerate(items)
        ],
    }


@app.post("/api/quiz/{attempt_id}/submit")
def submit_quiz(attempt_id: int, body: QuizSubmit, db: Session = Depends(get_db)):
    """Grade the quiz, set the tested skill levels, update readiness, and record a snapshot."""
    attempt = db.get(models.QuizAttempt, attempt_id)
    if not attempt:
        raise HTTPException(404, "Quiz not found.")
    if attempt.completed:
        raise HTTPException(409, "This quiz was already submitted. Start a new one.")

    items = json.loads(attempt.payload)
    if len(body.answers) != len(items):
        raise HTTPException(422, f"Expected {len(items)} answers, got {len(body.answers)}.")
    for i, chosen in enumerate(body.answers):
        if not 0 <= chosen < len(items[i]["options"]):
            raise HTTPException(422, f"Answer {i + 1} is not a valid option.")

    student = _get_student(db, attempt.student_id)
    readiness_before = analyze_student(db, student)["readiness"]

    graded = grade_attempt(items, body.answers)

    name_to_id = {s.name: s.id for s in db.scalars(select(models.Skill)).all()}
    existing = {ss.skill_id: ss for ss in student.skills}
    skill_results = []

    for name in sorted(graded["skills"]):
        stats = graded["skills"][name]
        skill_id = name_to_id[name]
        previous = existing[skill_id].level if skill_id in existing else 0
        new_level = stats["level"]
        if skill_id in existing:
            existing[skill_id].level = new_level
        else:
            student.skills.append(models.StudentSkill(skill_id=skill_id, level=new_level))
        skill_results.append(
            {
                "skill": name,
                "correct": stats["correct"],
                "total": stats["total"],
                "previous_level": previous,
                "level": new_level,
                "label": LEVEL_LABELS[new_level],
            }
        )

    db.flush()
    readiness_after = analyze_student(db, student)["readiness"]

    attempt.completed = True
    db.add(
        models.ProgressSnapshot(
            student_id=student.id,
            role_id=attempt.role_id,
            readiness=readiness_after,
        )
    )
    db.commit()

    return {
        "score": graded["score"],
        "total": graded["total"],
        "readiness_before": readiness_before,
        "readiness": readiness_after,
        "skills": skill_results,
        "review": graded["review"],
    }


# ---------- web page ----------

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")

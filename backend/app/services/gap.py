from sqlalchemy import select
from sqlalchemy.orm import joinedload

from .. import models

LEVEL_LABELS = ["Not started", "Aware", "Beginner", "Practicing", "Proficient", "Expert"]
PHASE_SIZE = 3
WEEKS_PER_PHASE = 4


def build_roadmap(missing):
    """Group ranked gaps into phases of three skills each."""
    phases = []
    for start in range(0, len(missing), PHASE_SIZE):
        chunk = missing[start:start + PHASE_SIZE]
        index = len(phases)
        phases.append(
            {
                "phase": index + 1,
                "weeks": f"Weeks {index * WEEKS_PER_PHASE + 1} to {(index + 1) * WEEKS_PER_PHASE}",
                "items": [
                    {
                        "skill": r["skill"],
                        "from_label": r["current_label"],
                        "to_label": r["required_label"],
                        "resource": r["resource"],
                        "estimated_weeks": max(1, r["gap"] * 2),
                    }
                    for r in chunk
                ],
            }
        )
    return phases


def analyze_student(db, student):
    levels = {ss.skill_id: ss.level for ss in student.skills}
    rows = []
    total_weight = 0
    achieved = 0

    for req in student.target_role.requirements:
        current = levels.get(req.skill_id, 0)
        gap = max(0, req.required_level - current)
        total_weight += req.required_level * req.importance
        achieved += min(current, req.required_level) * req.importance
        rows.append(
            {
                "skill_id": req.skill_id,
                "skill": req.skill.name,
                "category": req.skill.category,
                "resource": req.skill.resource,
                "current": current,
                "current_label": LEVEL_LABELS[current],
                "required": req.required_level,
                "required_label": LEVEL_LABELS[req.required_level],
                "importance": req.importance,
                "gap": gap,
                "priority": gap * req.importance,
                "rank": None,
            }
        )

    readiness = round(100 * achieved / total_weight, 1) if total_weight else 0.0

    # Priority = gap x importance. Biggest, most important gaps first.
    rows.sort(key=lambda r: (-r["priority"], -r["importance"], r["skill"]))
    missing = [r for r in rows if r["gap"] > 0]
    for i, row in enumerate(missing, start=1):
        row["rank"] = i

    projects = (
        db.scalars(select(models.Project).options(joinedload(models.Project.skills)))
        .unique()
        .all()
    )
    missing_ids = {r["skill_id"] for r in missing}
    recommendations = []
    for project in projects:
        covered = [s for s in project.skills if s.id in missing_ids]
        if covered:
            recommendations.append(
                {
                    "id": project.id,
                    "title": project.title,
                    "description": project.description,
                    "difficulty": project.difficulty,
                    "covers": [s.name for s in covered],
                    "closes_count": len(covered),
                }
            )
    recommendations.sort(key=lambda p: -p["closes_count"])

    return {
        "role": {"id": student.target_role.id, "title": student.target_role.title},
        "readiness": readiness,
        "summary": {
            "total_skills": len(rows),
            "ready_skills": len(rows) - len(missing),
            "gap_skills": len(missing),
        },
        "skills": rows,
        "roadmap": build_roadmap(missing),
        "projects": recommendations[:5],
    }

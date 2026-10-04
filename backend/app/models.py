from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base

project_skills = Table(
    "project_skills",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(60), nullable=False)
    resource = Column(Text, nullable=False, default="")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    title = Column(String(120), unique=True, nullable=False)
    description = Column(Text, nullable=False, default="")
    requirements = relationship(
        "RoleRequirement", back_populates="role", cascade="all, delete-orphan"
    )


class RoleRequirement(Base):
    __tablename__ = "role_requirements"
    __table_args__ = (UniqueConstraint("role_id", "skill_id"),)

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    required_level = Column(Integer, nullable=False)  # 1-5
    importance = Column(Integer, nullable=False)  # 1-5

    role = relationship("Role", back_populates="requirements")
    skill = relationship("Skill")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    title = Column(String(150), unique=True, nullable=False)
    description = Column(Text, nullable=False, default="")
    difficulty = Column(String(20), nullable=False, default="Medium")
    skills = relationship("Skill", secondary=project_skills)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    target_role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    target_role = relationship("Role")
    skills = relationship(
        "StudentSkill", back_populates="student", cascade="all, delete-orphan"
    )


class StudentSkill(Base):
    __tablename__ = "student_skills"
    __table_args__ = (UniqueConstraint("student_id", "skill_id"),)

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    level = Column(Integer, nullable=False, default=0)  # 0-5

    student = relationship("Student", back_populates="skills")
    skill = relationship("Skill")


class ProgressSnapshot(Base):
    __tablename__ = "progress_snapshots"

    id = Column(Integer, primary_key=True)
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    readiness = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class QuizAttempt(Base):
    """One quiz sitting. Stores the shuffled questions and the answer key on the server."""

    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True)
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    payload = Column(Text, nullable=False)  # JSON list of questions with correct answers
    completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

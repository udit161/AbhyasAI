from datetime import datetime, timezone
import uuid
from typing import List, Optional, Any, Dict
from sqlalchemy import String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    """
    User database model representing students, candidates, and instructors.
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="instructor", cascade="all, delete-orphan")
    session_histories: Mapped[List["SessionHistory"]] = relationship("SessionHistory", back_populates="user", cascade="all, delete-orphan")


class Course(Base):
    """
    Course database model representing learning modules.
    """
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    instructor: Mapped["User"] = relationship("User", back_populates="courses")
    videos: Mapped[List["Video"]] = relationship("Video", back_populates="course", cascade="all, delete-orphan")
    session_histories: Mapped[List["SessionHistory"]] = relationship("SessionHistory", back_populates="course")


class Video(Base):
    """
    Video database model containing timestamps and transcript information.
    """
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    video_url: Mapped[str] = mapped_column(String(512), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    transcript_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="videos")
    session_histories: Mapped[List["SessionHistory"]] = relationship("SessionHistory", back_populates="video")


class SessionHistory(Base):
    """
    SessionHistory database model storing user interaction histories (chat, quiz, interview).
    """
    __tablename__ = "session_histories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    course_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("courses.id"), index=True, nullable=True)
    video_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("videos.id"), index=True, nullable=True)
    session_type: Mapped[str] = mapped_column(String(50), nullable=False, default="chat") # chat, quiz, interview
    history_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    scorecard: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="session_histories")
    course: Mapped[Optional["Course"]] = relationship("Course", back_populates="session_histories")
    video: Mapped[Optional["Video"]] = relationship("Video", back_populates="session_histories")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.models.db_models import User, Course, Video, SessionHistory


@pytest.fixture
def db_session():
    """
    Creates an in-memory SQLite database session for testing DB models.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_create_user_course_video_and_session(db_session):
    """
    Test creating relational records for User, Course, Video, and SessionHistory.
    """
    # 1. Create Instructor User
    user = User(
        email="instructor@abhyas.ai",
        full_name="Dr. Alex Rivera",
        hashed_password="securepassword123",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "instructor@abhyas.ai"

    # 2. Create Course
    course = Course(
        title="Fullstack AI Engineering & RAG Systems",
        description="Comprehensive course on FastAPI, Vector Databases, and LLM Grounding",
        instructor_id=user.id,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    assert course.id is not None
    assert course.instructor_id == user.id

    # 3. Create Video
    video = Video(
        course_id=course.id,
        title="Lecture 1: Vector Stores and Metadata Filtering",
        video_url="https://s3.amazonaws.com/abhyas-courses/lecture1.mp4",
        duration_seconds=1800.0,
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)

    assert video.id is not None
    assert video.course_id == course.id

    # 4. Create SessionHistory
    session_history = SessionHistory(
        user_id=user.id,
        course_id=course.id,
        video_id=video.id,
        session_type="chat",
        history_data={
            "messages": [
                {"role": "user", "content": "What is vector metadata filtering?"},
                {"role": "assistant", "content": "Vector metadata filtering limits vector search to specific timestamps or pages."}
            ]
        },
    )
    db_session.add(session_history)
    db_session.commit()
    db_session.refresh(session_history)

    assert session_history.id is not None
    assert session_history.user_id == user.id
    assert session_history.session_type == "chat"
    assert len(session_history.history_data["messages"]) == 2

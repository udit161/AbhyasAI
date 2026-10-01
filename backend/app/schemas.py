from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class ChatAskRequest(BaseModel):
    """
    Pydantic Schema for incoming chat question requests.
    Validates required fields and data types.
    """
    course_id: str = Field(
        ..., 
        description="ID of the course being watched",
        json_schema_extra={"example": "course_101"}
    )
    video_id: str = Field(
        ..., 
        description="ID of the video being watched",
        json_schema_extra={"example": "video_202"}
    )
    current_timestamp: float = Field(
        ..., 
        ge=0.0, 
        description="Current playback position of the video in seconds",
        json_schema_extra={"example": 120.5}
    )
    question: str = Field(
        ..., 
        min_length=1, 
        description="Question asked by the user",
        json_schema_extra={"example": "What is FastAPI?"}
    )

class ChatAskResponse(BaseModel):
    """
    Pydantic Schema for the mock response returned by Phase 1 endpoint.
    """
    status: str = Field(default="success", description="Status of the request")
    is_mock: bool = Field(default=True, description="Flag indicating mock response mode")
    message: str = Field(..., description="Description label of response mode")
    course_id: str = Field(..., description="Echoed course ID")
    video_id: str = Field(..., description="Echoed video ID")
    current_timestamp: float = Field(..., description="Echoed video timestamp in seconds")
    question: str = Field(..., description="Echoed question text")
    mock_answer: str = Field(..., description="Generated mock answer string")

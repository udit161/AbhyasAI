from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ResourceType(str, Enum):
    VIDEO = "video"
    PDF = "pdf"
    PPT = "ppt"
    NOTE = "note"


class VectorMetadata(BaseModel):
    """
    Schema for vector document metadata supporting exact timestamp ranges,
    PDF page numbers, and PPT slide indices for precision RAG filtering.
    """
    resource_id: str = Field(..., description="ID of the video, PDF, or PPT document")
    course_id: Optional[str] = Field(None, description="Associated course ID")
    resource_type: ResourceType = Field(..., description="Type of resource: video, pdf, ppt, or note")
    title: str = Field(..., description="Title of the resource or document")
    text_chunk: str = Field(..., description="Text content chunk embedded into vector store")
    
    # Video-specific metadata filtering fields
    start_time: Optional[float] = Field(None, description="Start timestamp of video segment in seconds")
    end_time: Optional[float] = Field(None, description="End timestamp of video segment in seconds")
    
    # PDF-specific metadata filtering field
    page_number: Optional[int] = Field(None, description="PDF page number (1-indexed)")
    
    # PPT-specific metadata filtering field
    slide_index: Optional[int] = Field(None, description="PPT slide index (1-indexed)")
    
    # Chunk ordering & indexing
    chunk_index: int = Field(0, description="Sequential index of chunk in document")


class VectorDocument(BaseModel):
    """
    Vector document record containing document ID, optional embedding vector, and metadata.
    """
    id: str
    content: str
    metadata: VectorMetadata
    embedding: Optional[List[float]] = None


class VectorFilterQuery(BaseModel):
    """
    Query parameters and metadata filters for vector similarity search.
    """
    query_text: str
    video_id: Optional[str] = None
    course_id: Optional[str] = None
    max_timestamp: Optional[float] = Field(None, description="Filter video segments where start_time <= max_timestamp")
    min_timestamp: Optional[float] = Field(None, description="Filter video segments where end_time >= min_timestamp")
    page_number: Optional[int] = Field(None, description="Filter PDF chunks for specific page")
    slide_index: Optional[int] = Field(None, description="Filter PPT chunks for specific slide index")
    allowed_resource_ids: Optional[List[str]] = Field(None, description="Filter by list of authorized resource IDs")
    resource_types: Optional[List[ResourceType]] = None
    top_k: int = Field(5, ge=1, le=50, description="Number of vector search results to retrieve")

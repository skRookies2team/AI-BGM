"""
Pydantic models for Music Streaming API
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class AnalyzeRequest(BaseModel):
    """Request model for /api/analyze endpoint"""
    prompt: str = Field(..., min_length=1, description="Scene description to analyze")


class MusicAnalysis(BaseModel):
    """GPT analysis result"""
    primary_mood: str = Field(..., description="Primary mood detected")
    secondary_mood: Optional[str] = Field(None, description="Secondary mood if any")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Intensity level 0.0-1.0")
    emotional_tags: List[str] = Field(default_factory=list, description="List of emotional tags")
    reasoning: str = Field(..., description="Reasoning for mood selection")


class MusicInfo(BaseModel):
    """Music file information"""
    mood: str = Field(..., description="Selected mood")
    filename: str = Field(..., description="Music filename")
    file_path: str = Field(..., description="Full path in GCS")
    streaming_url: str = Field(..., description="GCS signed streaming URL")


class AnalyzeResponse(BaseModel):
    """Response model for /api/analyze endpoint"""
    analysis: MusicAnalysis
    music: MusicInfo


class MoodInfo(BaseModel):
    """Mood configuration information"""
    keywords: List[str] = Field(..., description="Korean keywords for this mood")
    folders: List[str] = Field(..., description="GCS folders associated with this mood")


class HealthResponse(BaseModel):
    """Response model for /api/health endpoint"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    gcs_bucket: str = Field(..., description="GCS bucket name")
    total_files: int = Field(..., description="Total number of music files")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")

"""Health check response schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Standard health check payload returned by all health endpoints."""

    status: str = Field(default="healthy", examples=["healthy"])
    service: str = Field(default="RetainAI API", examples=["RetainAI API"])
    environment: str = Field(examples=["development"])
    version: str = Field(examples=["0.1.0"])

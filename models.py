from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

# Type alias for space status
SpaceStatusEnum = Literal["online", "degraded", "offline", "unknown"]

class SpaceStatus(BaseModel):
    """Model representing the status of a monitored space."""
    id: str
    name: str
    status: SpaceStatusEnum
    response_time_ms: Optional[float] = None
    last_check: datetime
    last_error: Optional[str] = None

class LogEntry(BaseModel):
    """Model representing a log entry for a space."""
    timestamp: datetime
    space_id: str
    level: Literal["INFO", "WARNING", "ERROR", "CRITICAL"]
    message: str

class HistoryPoint(BaseModel):
    """Model representing a historical data point."""
    timestamp: str
    response_time: Optional[float]
    status: str
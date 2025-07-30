"""Pydantic models for OJP requests and responses."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class Coordinates(BaseModel):
    """Geographic coordinates."""
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)

class Location(BaseModel):
    """A location (stop, POI, or address)."""
    id: Optional[str] = None
    name: str
    coordinates: Optional[Coordinates] = None
    type: Literal["stop", "poi", "address"] = "stop"
    probability: Optional[float] = Field(None, ge=0, le=1, description="Search result probability/relevance score")

class TripRequestParams(BaseModel):
    """Parameters for a trip request."""
    origin: str = Field(..., description="Origin location name or coordinates")
    destination: str = Field(..., description="Destination location name or coordinates")
    origin_stop_point_ref: str = Field(..., description="Origin stop point reference")
    destination_stop_point_ref: str = Field(..., description="Destination stop point reference")
    departure_time: Optional[datetime] = Field(None, description="Preferred departure time. UTC")
    arrival_time: Optional[datetime] = Field(None, description="Preferred arrival time. UTC")
    transport_modes: List[str] = Field(default=["public_transport"], description="Transport modes to use")
    max_results: int = Field(default=5, ge=1, le=20)
    include_accessibility: bool = Field(default=False, description="Include accessibility information")

class LocationSearchParams(BaseModel):
    """Parameters for location search."""
    query: Optional[str] = Field(None, description="Search query text")
    coordinates: Optional[Coordinates] = Field(None, description="Search center coordinates")
    radius: int = Field(default=1000, ge=50, le=10000, description="Search radius in meters")
    location_types: List[str] = Field(default=["stop"], description="Types of locations to find")
    max_results: int = Field(default=10, ge=1, le=50)

class Leg(BaseModel):
    """A journey leg."""
    mode: str
    origin: Location
    destination: Location
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    distance_meters: Optional[int] = None
    line_name: Optional[str] = None
    direction: Optional[str] = None

class Trip(BaseModel):
    """A complete trip with multiple legs."""
    legs: List[Leg]
    total_duration_minutes: int
    total_distance_meters: Optional[int] = None
    departure_time: datetime
    arrival_time: datetime
    transfers: int
    accessibility_info: Optional[Dict[str, Any]] = None

class OJPResponse(BaseModel):
    """Base OJP response."""
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class TripResponse(OJPResponse):
    """Response for trip requests."""
    trips: List[Trip] = Field(default_factory=list)


class LocationResponse(OJPResponse):
    """Response for location searches."""
    locations: List[Location] = Field(default_factory=list)
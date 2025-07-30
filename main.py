import asyncio
from datetime import datetime
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from ojp.client import get_ojp_client
from ojp.models import (
    TripRequestParams, LocationSearchParams
)

# Create an MCP server
mcp = FastMCP("OJP Swiss Transport")

class TripRequestMandatoryParams(BaseModel):
    origin: str = Field(..., description="Origin location (name)")
    destination: str = Field(..., description="Destination location (name)")
    origin_stop_point_ref: str = Field(..., description="Origin stop point reference")
    destination_stop_point_ref: str = Field(..., description="Destination stop point reference")

async def _trip_request_internal(
    origin: str,
    destination: str,
    origin_stop_point_ref: str,
    destination_stop_point_ref: str,
    departure_time: Optional[str] = None,
    transport_modes: List[str] = ["public_transport"],
    max_results: int = 5
) -> dict:
    """Plan a journey between two locations using Swiss public transport and other modes.
    
    This tool uses the Open Journey Planner (OJP) API to find the best routes between 
    an origin and destination. It supports multi-modal transport including bus, tram, train,
    walking, cycling, and car travel.
    """
    try:
        # Parse departure time if provided
        departure_dt = None
        if departure_time:
            try:
                departure_dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid departure time format. Use YYYY-MM-DDTHH:MM:SS format."
                }
        
        # Create request parameters
        params = TripRequestParams(
            origin=origin,
            destination=destination,
            origin_stop_point_ref=origin_stop_point_ref,
            destination_stop_point_ref=destination_stop_point_ref,
            arrival_time=None,  # Not used in this request
            departure_time=departure_dt,
            transport_modes=transport_modes,
            max_results=max_results
        )
        
        # Get OJP client and make request
        client = get_ojp_client()
        response = await client.trip_request(params)
        
        # Convert response to dict for JSON serialization
        result = {
            "success": response.success,
            "timestamp": response.timestamp.isoformat(),
            "trips": []
        }
        
        if response.error_message:
            result["error"] = response.error_message
        
        for trip in response.trips:
            trip_dict = {
                "departure_time": trip.departure_time.isoformat() if trip.departure_time else None,
                "arrival_time": trip.arrival_time.isoformat() if trip.arrival_time else None,
                "total_duration_minutes": trip.total_duration_minutes,
                "transfers": trip.transfers,
                "legs": []
            }
            
            for leg in trip.legs:
                leg_dict = {
                    "mode": leg.mode,
                    "origin": {
                        "name": leg.origin.name,
                        "coordinates": {
                            "longitude": leg.origin.coordinates.longitude,
                            "latitude": leg.origin.coordinates.latitude
                        } if leg.origin.coordinates else None
                    },
                    "destination": {
                        "name": leg.destination.name,
                        "coordinates": {
                            "longitude": leg.destination.coordinates.longitude,
                            "latitude": leg.destination.coordinates.latitude
                        } if leg.destination.coordinates else None
                    },
                    "departure_time_utc": leg.departure_time.isoformat() if leg.departure_time else None,
                    "arrival_time_utc": leg.arrival_time.isoformat() if leg.arrival_time else None,
                    "duration_minutes": leg.duration_minutes,
                    "line_name": leg.line_name,
                    "direction": leg.direction
                }
                trip_dict["legs"].append(leg_dict)
            
            result["trips"].append(trip_dict)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

@mcp.tool()
async def trip_request(
    mandatory_params: TripRequestMandatoryParams,
    departure_time: Optional[str] = Field(None, description="Departure time in ISO format (YYYY-MM-DDTHH:MM:SS). If not provided, uses current time."),
    transport_modes: List[str] = Field(default=["public_transport"], description="Transport modes: public_transport, walking, cycling, car"),
    max_results: int = Field(default=5, description="Maximum number of trip results to return")
) -> dict:
    """Plan a journey between two locations using Swiss public transport and other modes.
    
    This tool uses the Open Journey Planner (OJP) API to find the best routes between 
    an origin and destination. It supports multi-modal transport including public transport,
    walking, cycling, and car travel.
    """
    return await _trip_request_internal(
        origin=mandatory_params.origin,
        destination=mandatory_params.destination,
        origin_stop_point_ref=mandatory_params.origin_stop_point_ref,
        destination_stop_point_ref=mandatory_params.destination_stop_point_ref,
        departure_time=departure_time,
        transport_modes=transport_modes,
        max_results=max_results
    )

@mcp.tool()
async def location_search(
    query: str = Field(..., description="Search query for locations (station names, addresses, POIs)"),
    max_results: int = Field(default=10, description="Maximum number of results to return")
) -> dict:
    """Search for locations such as train stations, bus stops, addresses, and points of interest.
    
    This tool helps you find specific locations in Switzerland and neighboring countries.
    It's useful for getting exact location names and IDs for trip planning.
    
    Examples:
    - location_search(query="Zurich")
    - location_search(query="Bern Hauptbahnhof") 
    - location_search(query="Geneva Airport")
    """
    try:
        # Create request parameters
        params = LocationSearchParams(
            query=query,
            coordinates=None,  # Not used in this request
            max_results=max_results
        )
        
        # Get OJP client and make request
        client = get_ojp_client()
        response = await client.location_search(params)
        
        # Convert response to dict
        result = {
            "success": response.success,
            "timestamp": response.timestamp.isoformat(),
            "locations": []
        }
        
        if response.error_message:
            result["error"] = response.error_message
        
        for location in response.locations:
            location_dict = {
                "stop_point_reference": location.id,
                "name": location.name,
                "type": location.type,
                "coordinates": {
                    "longitude": location.coordinates.longitude,
                    "latitude": location.coordinates.latitude
                } if location.coordinates else None
            }
            result["locations"].append(location_dict)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

if __name__ == "__main__":
    mcp.run("streamable-http")
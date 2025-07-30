"""OJP API client for making HTTP requests to the Open Journey Planner API."""

import os
import httpx
from typing import Optional
from dotenv import load_dotenv

from .models import (
    TripRequestParams, LocationSearchParams,
    TripResponse, LocationResponse
)
from .xml_templates import (
    get_trip_request_xml, get_location_request_xml
)
from .parsers import OJPParser

# Load environment variables from .env file
load_dotenv()

# Configuration constants from environment variables
OJP_V2_ENDPOINT = os.getenv("OJP_V2_ENDPOINT", "https://api.opentransportdata.swiss/ojp20")
OJP_API_KEY = os.getenv("OJP_API_KEY", "")
DEFAULT_REQUESTOR_REF = os.getenv("DEFAULT_REQUESTOR_REF", "MCP_OJP_Client_prod")
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))


class OJPClient:
    """Client for interacting with the OJP API."""
    
    def __init__(
        self,
        api_key: str = OJP_API_KEY,
        endpoint: str = OJP_V2_ENDPOINT,
        requestor_ref: str = DEFAULT_REQUESTOR_REF,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """Initialize the OJP client."""
        self.api_key = api_key
        self.endpoint = endpoint
        self.requestor_ref = requestor_ref
        self.timeout = timeout
        
        self.headers = {
            "Content-Type": "application/xml",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def trip_request(self, params: TripRequestParams) -> TripResponse:
        """Request trip planning between origin and destination."""
        try:
            # Generate XML request
            xml_request = get_trip_request_xml(
                origin=params.origin,
                destination=params.destination,
                origin_stop_point_ref=params.origin_stop_point_ref,
                destination_stop_point_ref=params.destination_stop_point_ref,
                departure_time=params.departure_time,
                transport_modes=params.transport_modes,
                requestor_ref=self.requestor_ref,
                max_results=params.max_results,
            )
            
            # Make HTTP request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    content=xml_request,
                    headers=self.headers
                )
                response.raise_for_status()
            
            # Parse response
            return OJPParser.parse_trip_response(response.text)
            
        except httpx.HTTPStatusError as e:
            return TripResponse(
                success=False,
                error_message=f"HTTP error {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            return TripResponse(
                success=False,
                error_message=f"Request error: {str(e)}"
            )
        except Exception as e:
            return TripResponse(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def location_search(self, params: LocationSearchParams) -> LocationResponse:
        """Search for locations (stops, POIs, addresses)."""
        try:
            if not params.query:
                return LocationResponse(
                    success=False,
                    error_message="Query parameter is required for location search"
                )
            
            # Generate XML request
            xml_request = get_location_request_xml(
                query=params.query,
                requestor_ref=self.requestor_ref
            )
            
            # Make HTTP request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    content=xml_request,
                    headers=self.headers
                )
                response.raise_for_status()
            
            # Parse response
            return OJPParser.parse_location_response(response.text)
            
        except httpx.HTTPStatusError as e:
            return LocationResponse(
                success=False,
                error_message=f"HTTP error {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            return LocationResponse(
                success=False,
                error_message=f"Request error: {str(e)}"
            )
        except Exception as e:
            return LocationResponse(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )

# Global client instance
_ojp_client: Optional[OJPClient] = None


def get_ojp_client() -> OJPClient:
    """Get the global OJP client instance."""
    global _ojp_client
    if _ojp_client is None:
        _ojp_client = OJPClient()
    return _ojp_client

#!/usr/bin/env python3
"""Test script for OJP trip planning to check number of results."""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ojp.client import get_ojp_client
from ojp.models import TripRequestParams


async def test_trip_request():
    """Test the trip request functionality."""
    print("Testing trip request...")
    
    client = get_ojp_client()
    
    # Use sample parameters for a trip from Zurich Giesshübel to Zurich HB
    # (matching the sample response XML)
    departure_time = datetime.now() + timedelta(minutes=10)
    
    params = TripRequestParams(
        origin="Zürich Giesshübel",
        destination="Zürich HB", 
        origin_stop_point_ref="8503091",
        destination_stop_point_ref="8503000",
        departure_time=departure_time,
        arrival_time=None,  # Not using arrival time constraint
        transport_modes=["public_transport"],
        max_results=3
    )
    
    try:
        response = await client.trip_request(params)
        print(f"Success: {response.success}")
        if response.success:
            print(f"Found {len(response.trips)} trip options:")
            for i, trip in enumerate(response.trips, 1):
                print(f"  Option {i}:")
                print(f"    Departure: {trip.departure_time.strftime('%H:%M') if trip.departure_time else 'N/A'}")
                print(f"    Arrival: {trip.arrival_time.strftime('%H:%M') if trip.arrival_time else 'N/A'}")
                print(f"    Duration: {trip.total_duration_minutes} minutes")
                print(f"    Transfers: {trip.transfers}")
                print(f"    Legs: {len(trip.legs)}")
                print()
        else:
            print(f"Error: {response.error_message}")
    except Exception as e:
        print(f"Exception: {e}")


async def main():
    """Run tests."""
    print("OJP Trip Request Test")
    print("=====================")
    
    await test_trip_request()


if __name__ == "__main__":
    asyncio.run(main())

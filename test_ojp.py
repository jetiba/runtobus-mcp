#!/usr/bin/env python3
"""Test script for OJP MCP tools."""

import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ojp.client import get_ojp_client
from ojp.models import LocationSearchParams


async def test_location_search():
    """Test the location search functionality."""
    print("Testing location search...")
    
    client = get_ojp_client()
    params = LocationSearchParams(query="Zurich")
    
    try:
        response = await client.location_search(params)
        print(f"Success: {response.success}")
        if response.success:
            print(f"Found {len(response.locations)} locations:")
            for loc in response.locations[:3]:  # Show first 3
                print(f"  - {loc.name} (ID: {loc.id})")
        else:
            print(f"Error: {response.error_message}")
    except Exception as e:
        print(f"Exception: {e}")


async def main():
    """Run tests."""
    print("OJP MCP Tools Test")
    print("==================")
    
    await test_location_search()


if __name__ == "__main__":
    asyncio.run(main())

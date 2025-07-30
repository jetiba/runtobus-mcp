# Swiss Transport Sample MCP Server

> **_NOTE:_**
> This is a sample MCP server created for demonstration and educational purposes only. It is not an official MCP server for Swiss Transportation services.

:question: Did you ever think you’d be able to check public transport times directly in VS Code, without breaking your development flow?

Here there is a sample of a Model Context Protocol (MCP) server that provides access to Swiss public transport data through the Open Journey Planner (OJP) API. This server enables AI assistants to search for locations and plan multi-modal journeys across Switzerland and neighboring countries.

## :computer: Features

- **Location Search**: Find train stations, bus stops, addresses, and points of interest
- **Trip Planning**: Plan journeys using public transport, walking, cycling, and car travel
- **Multi-modal Transport**: Support for buses, trams, trains, walking, cycling, and car routes
- **Real-time Data**: Access to current Swiss public transport schedules and routing
- **Comprehensive Coverage**: Switzerland and neighboring countries

## :wrench: Available Tools

### 1. `location_search`
Search for locations such as train stations, bus stops, addresses, and points of interest.

**Parameters:**
- `query` (required): Search query for locations (station names, addresses, POIs)
- `max_results` (optional): Maximum number of results to return (default: 10)

**Example Usage:**
```
location_search(query="Zurich Hauptbahnhof")
location_search(query="Geneva Airport")
location_search(query="Bern")
```

### 2. `trip_request`
Plan a journey between two locations using Swiss public transport and other modes.

**Parameters:**
- `mandatory_params` (required): Object containing:
  - `origin`: Origin location name
  - `destination`: Destination location name  
  - `origin_stop_point_ref`: Origin stop point reference (from location search)
  - `destination_stop_point_ref`: Destination stop point reference (from location search)
- `departure_time` (optional): Departure time in ISO format (YYYY-MM-DDTHH:MM:SS)
- `transport_modes` (optional): List of transport modes (default: ["public_transport"])
- `max_results` (optional): Maximum number of trip results to return (default: 5)

**Transport Modes:**
- `public_transport`: Buses, trams, trains
- `walking`: Walking routes
- `cycling`: Bicycle routes  
- `car`: Car routes

**Example Usage:**
First, search for locations to get their stop point references:
```
location_search(query="Zurich Hauptbahnhof")
location_search(query="Geneva")
```

Then plan a trip using the stop point references:
```
trip_request(
  mandatory_params={
    "origin": "Zurich Hauptbahnhof",
    "destination": "Geneva",
    "origin_stop_point_ref": "8503000",
    "destination_stop_point_ref": "8501008"
  },
  departure_time="2024-12-25T14:30:00",
  transport_modes=["public_transport"]
)
```

## Installation

### Prerequisites
- Python 3.13 or higher
- OJP API key from [Swiss Open Transport Data](https://opentransportdata.swiss/)

### Setup

1. Clone this repository:
```bash
git clone <repository-url>
cd mcpsrv
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Create a `.env` file in the project root with your OJP API configuration:
```env
OJP_API_KEY=your_api_key_here
OJP_V2_ENDPOINT=https://api.opentransportdata.swiss/ojp20
DEFAULT_REQUESTOR_REF=MCP_OJP_Client_prod
DEFAULT_TIMEOUT=30
```

4. Run the server:
```bash
uv run main.py
```

The server will start on the default MCP streamable HTTP port.

## :pencil2: Configuration

The server can be configured through environment variables:

- `OJP_API_KEY`: Your OJP API key (required)
- `OJP_V2_ENDPOINT`: OJP API endpoint (default: https://api.opentransportdata.swiss/ojp20)
- `DEFAULT_REQUESTOR_REF`: Client identifier for API requests (default: MCP_OJP_Client_prod)
- `DEFAULT_TIMEOUT`: HTTP request timeout in seconds (default: 30)

## Project Structure

```
mcpsrv/
├── main.py                 # MCP server entry point and tool definitions
├── pyproject.toml         # Project configuration and dependencies
├── definition.yaml        # MCP server definition for Copilot Studio
├── README.md              # This file
├── sample_response.xml    # Example OJP API response
├── test_*.py             # Test files
└── ojp/                  # OJP client library
    ├── __init__.py
    ├── client.py         # HTTP client for OJP API
    ├── models.py         # Pydantic data models
    ├── parsers.py        # XML response parsers
    └── xml_templates.py  # XML request templates
```

## API Response Format

### Location Search Response
```json
{
  "success": true,
  "timestamp": "2024-12-25T10:00:00Z",
  "locations": [
    {
      "stop_point_reference": "8503000",
      "name": "Zürich HB",
      "type": "stop",
      "coordinates": {
        "longitude": 8.540192,
        "latitude": 47.378177
      }
    }
  ]
}
```

### Trip Request Response
```json
{
  "success": true,
  "timestamp": "2024-12-25T10:00:00Z",
  "trips": [
    {
      "departure_time": "2024-12-25T14:30:00Z",
      "arrival_time": "2024-12-25T17:15:00Z", 
      "total_duration_minutes": 165,
      "transfers": 1,
      "legs": [
        {
          "mode": "train",
          "origin": {
            "name": "Zürich HB",
            "coordinates": {"longitude": 8.540192, "latitude": 47.378177}
          },
          "destination": {
            "name": "Genève",
            "coordinates": {"longitude": 6.142296, "latitude": 46.210033}
          },
          "departure_time_utc": "2024-12-25T14:30:00Z",
          "arrival_time_utc": "2024-12-25T17:15:00Z",
          "duration_minutes": 165,
          "line_name": "IC 1",
          "direction": "Genève-Aéroport"
        }
      ]
    }
  ]
}
```

## Error Handling

The server provides comprehensive error handling:

- **Invalid API Key**: Returns authentication error
- **Invalid Location**: Returns location not found error
- **Network Issues**: Returns connection error with details
- **Malformed Requests**: Returns validation error with specific field issues
- **API Rate Limits**: Returns rate limit exceeded error

## Testing

Run the test suite:
```bash
# Run specific tests
python test_ojp.py
python test_trip.py

# Or run all tests (if using pytest)
pytest
```

## Development

### Adding New Features

1. Define new data models in `ojp/models.py`
2. Add XML templates in `ojp/xml_templates.py`
3. Implement parsing logic in `ojp/parsers.py`
4. Add new client methods in `ojp/client.py`
5. Create MCP tools in `main.py`

### Code Style

This project uses:
- Type hints for better code documentation
- Pydantic for data validation
- Async/await for HTTP requests
- Environment variables for configuration

## License

[Add your license information here]

## Contributing

This project is licensed under the MIT License.

## Support

For issues related to:
- **OJP API**: Check [Swiss Open Transport Data documentation](https://opentransportdata.swiss/)
- **MCP Protocol**: See [Model Context Protocol documentation](https://modelcontextprotocol.io/)
- **This Server**: Open an issue in this repository
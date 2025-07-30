"""XML templates for OJP requests."""

from datetime import datetime, UTC
from typing import Optional


def get_trip_request_xml(
    origin: str,
    destination: str,
    origin_stop_point_ref: str,
    destination_stop_point_ref: str,
    max_results: int = 10,
    departure_time: Optional[datetime] = None,
    transport_modes: Optional[list] = None,
    requestor_ref: str = "MCP_OJP_Client_prod"
) -> str:
    """Generate XML for trip request."""
    if departure_time is None:
        departure_time = datetime.now(UTC)
    
    timestamp = departure_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    request_timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Generate mode filters based on transport_modes
    mode_filters = ""
    if transport_modes:
        # Map transport modes to OJP modes and determine what to exclude
        # For public_transport, we want to include all PT modes (don't exclude anything)
        # For specific modes, we might want to include only those
        if transport_modes == ["public_transport"] or "public_transport" in transport_modes:
            # Don't add any exclusion filters for public transport
            mode_filters = ""
        else:
            # For now, if specific modes are requested, don't exclude anything
            # This can be enhanced later to be more specific
            mode_filters = ""
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OJP xmlns="http://www.vdv.de/ojp" xmlns:siri="http://www.siri.org.uk/siri" version="2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.vdv.de/ojp OJP_changes_for_v1.1/OJP.xsd">
	<OJPRequest>
		<siri:ServiceRequest>
			<siri:RequestTimestamp>{request_timestamp}</siri:RequestTimestamp>
			<siri:RequestorRef>{requestor_ref}</siri:RequestorRef>
			<OJPTripRequest>
				<siri:RequestTimestamp>{request_timestamp}</siri:RequestTimestamp>
				<siri:MessageIdentifier>TR-1h2</siri:MessageIdentifier>
				<Origin>
					<PlaceRef>
						<siri:StopPointRef>{origin_stop_point_ref}</siri:StopPointRef>
						<n>
							<Text>{origin}</Text>
						</n>
					</PlaceRef>
                    <DepArrTime>{timestamp}</DepArrTime>
				</Origin>
				<Destination>
					<PlaceRef>
						<siri:StopPointRef>{destination_stop_point_ref}</siri:StopPointRef>
						<n>
							<Text>{destination}</Text>
						</n>
					</PlaceRef>
				</Destination>
				<Params>
					{mode_filters}
					<NumberOfResults>{max_results}</NumberOfResults>
				</Params>
			</OJPTripRequest>
		</siri:ServiceRequest>
	</OJPRequest>
</OJP>"""

def get_location_request_xml(
    query: str,
    requestor_ref: str = "MCP_OJP_Client_prod"
) -> str:
    """Generate XML for location information request."""
    request_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OJP xmlns="http://www.vdv.de/ojp" xmlns:siri="http://www.siri.org.uk/siri" version="2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.vdv.de/ojp ../../../../Downloads/OJP-changes_for_v1.1%20(1)/OJP-changes_for_v1.1/OJP.xsd">
    <OJPRequest>
        <siri:ServiceRequest>
            <siri:RequestTimestamp>{request_timestamp}</siri:RequestTimestamp>
            <siri:RequestorRef>{requestor_ref}</siri:RequestorRef>
            <OJPLocationInformationRequest>
                <siri:RequestTimestamp>{request_timestamp}</siri:RequestTimestamp>
                <siri:MessageIdentifier>LIR-1a</siri:MessageIdentifier>
                <InitialInput>
                    <Name>{query}</Name>
                </InitialInput>
                <Restrictions>
                    <Type>stop</Type>
                    <NumberOfResults>10</NumberOfResults>
                </Restrictions>
            </OJPLocationInformationRequest>
        </siri:ServiceRequest>
    </OJPRequest>
</OJP>"""
"""XML response parsers for OJP responses."""

from datetime import datetime
from typing import List, Optional
from lxml import etree # pyright: ignore[reportAttributeAccessIssue]
from dateutil import parser as date_parser

from .models import (
    Trip, Leg, Location, Coordinates,
    TripResponse, LocationResponse
)


class OJPParser:
    """Parser for OJP XML responses."""
    
    NAMESPACES = {
        'siri': 'http://www.siri.org.uk/siri',
        'ojp': 'http://www.vdv.de/ojp'
    }
    
    @classmethod
    def parse_trip_response(cls, xml_content: str) -> TripResponse:
        """Parse trip response XML."""
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            trips = []
            
            # Find all trip results
            trip_results = root.xpath('//ojp:TripResult', namespaces=cls.NAMESPACES)
            
            for trip_result in trip_results:
                trip = cls._parse_trip(trip_result)
                if trip:
                    trips.append(trip)
            
            return TripResponse(success=True, trips=trips)
            
        except Exception as e:
            return TripResponse(success=False, error_message=f"Failed to parse trip response: {str(e)}")
    
    @classmethod
    def parse_location_response(cls, xml_content: str) -> LocationResponse:
        """Parse location information response XML."""
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            locations = []
            
            # Find all place results in location information response
            place_results = root.xpath('//ojp:PlaceResult', namespaces=cls.NAMESPACES)
            
            for place_result in place_results:
                location = cls._parse_place_result(place_result)
                if location:
                    locations.append(location)
            
            return LocationResponse(success=True, locations=locations)
            
        except Exception as e:
            return LocationResponse(success=False, error_message=f"Failed to parse location response: {str(e)}")
    
    @classmethod
    def _parse_trip(cls, trip_elem) -> Optional[Trip]:
        """Parse a single trip element."""
        try:
            legs = []
            
            # Parse legs
            leg_elements = trip_elem.xpath('.//ojp:Leg', namespaces=cls.NAMESPACES)
            for leg_elem in leg_elements:
                leg = cls._parse_leg(leg_elem)
                if leg:
                    legs.append(leg)
            
            if not legs:
                return None
            
            # Calculate trip totals
            # Find first leg with departure time (may not be the first leg if it starts with walking)
            departure_time = None
            for leg in legs:
                if leg.departure_time:
                    departure_time = leg.departure_time
                    break
            
            # Find last leg with arrival time (may not be the last leg if it ends with walking)
            arrival_time = None
            for leg in reversed(legs):
                if leg.arrival_time:
                    arrival_time = leg.arrival_time
                    break
            
            # Calculate duration
            total_duration = 0
            if departure_time and arrival_time:
                total_duration = int((arrival_time - departure_time).total_seconds() / 60)
            else:
                # Fallback: sum individual leg durations
                for leg in legs:
                    if leg.duration_minutes:
                        total_duration += leg.duration_minutes
                    elif leg.departure_time and leg.arrival_time:
                        leg_duration = int((leg.arrival_time - leg.departure_time).total_seconds() / 60)
                        total_duration += leg_duration
            
            # Count transfers (number of public transport legs - 1)
            public_transport_legs = [leg for leg in legs if leg.mode not in ['walk', 'walking']]
            transfers = max(0, len(public_transport_legs) - 1)
            
            # Use first leg's departure time if no timed leg found
            if not departure_time:
                departure_time = legs[0].departure_time
            
            # Use last leg's arrival time if no timed leg found  
            if not arrival_time:
                arrival_time = legs[-1].arrival_time
            
            return Trip(
                legs=legs,
                total_duration_minutes=total_duration,
                departure_time=departure_time,
                arrival_time=arrival_time,
                transfers=transfers
            )
            
        except Exception:
            return None
    
    @classmethod
    def _parse_leg(cls, leg_elem) -> Optional[Leg]:
        """Parse a single leg element."""
        try:
            # Determine leg type and mode
            timed_leg = leg_elem.xpath('.//ojp:TimedLeg', namespaces=cls.NAMESPACES)
            continuous_leg = leg_elem.xpath('.//ojp:ContinuousLeg', namespaces=cls.NAMESPACES)
            transfer_leg = leg_elem.xpath('./ojp:TransferLeg', namespaces=cls.NAMESPACES)
            
            if timed_leg:
                return cls._parse_timed_leg(timed_leg[0])
            elif continuous_leg:
                return cls._parse_continuous_leg(continuous_leg[0])
            elif transfer_leg:
                return cls._parse_transfer_leg(leg_elem, transfer_leg[0])
            
            return None
            
        except Exception:
            return None
    
    @classmethod
    def _parse_timed_leg(cls, leg_elem) -> Optional[Leg]:
        """Parse a timed leg (public transport)."""
        try:
            # Get boarding and alighting information
            board_elem = leg_elem.xpath('.//ojp:LegBoard', namespaces=cls.NAMESPACES)
            alight_elem = leg_elem.xpath('.//ojp:LegAlight', namespaces=cls.NAMESPACES)
            
            if not board_elem or not alight_elem:
                return None
            
            # Get origin and destination locations
            origin = cls._parse_leg_board_alight(board_elem[0])
            destination = cls._parse_leg_board_alight(alight_elem[0])
            
            # Get departure and arrival times
            departure_time = None
            arrival_time = None
            
            # Extract departure time from ServiceDeparture
            dep_time_elem = board_elem[0].xpath('.//ojp:ServiceDeparture/ojp:EstimatedTime', namespaces=cls.NAMESPACES)
            if not dep_time_elem:
                dep_time_elem = board_elem[0].xpath('.//ojp:ServiceDeparture/ojp:TimetabledTime', namespaces=cls.NAMESPACES)
            if dep_time_elem:
                try:
                    departure_time = date_parser.parse(dep_time_elem[0].text)
                except Exception:
                    pass
            
            # Extract arrival time from ServiceArrival
            arr_time_elem = alight_elem[0].xpath('.//ojp:ServiceArrival/ojp:EstimatedTime', namespaces=cls.NAMESPACES)
            if not arr_time_elem:
                arr_time_elem = alight_elem[0].xpath('.//ojp:ServiceArrival/ojp:TimetabledTime', namespaces=cls.NAMESPACES)
            if arr_time_elem:
                try:
                    arrival_time = date_parser.parse(arr_time_elem[0].text)
                except Exception:
                    pass
            
            # Get service info and transport mode
            service = leg_elem.xpath('.//ojp:Service', namespaces=cls.NAMESPACES)
            line_name = None
            direction = None
            mode = "public_transport"  # default fallback
            
            if service:
                # Try PublishedServiceName first (e.g., "S4", "200")
                line_elem = service[0].xpath('.//ojp:PublishedServiceName/ojp:Text', namespaces=cls.NAMESPACES)
                if line_elem:
                    line_name = line_elem[0].text
                
                # Fallback to PublicCode if no PublishedServiceName
                if not line_name:
                    code_elem = service[0].xpath('.//ojp:PublicCode', namespaces=cls.NAMESPACES)
                    if code_elem:
                        line_name = code_elem[0].text
                
                direction_elem = service[0].xpath('.//ojp:DestinationText/ojp:Text', namespaces=cls.NAMESPACES)
                if direction_elem:
                    direction = direction_elem[0].text
                
                # Extract transport mode from Mode/PtMode
                mode_elem = service[0].xpath('.//ojp:Mode/ojp:PtMode', namespaces=cls.NAMESPACES)
                if mode_elem:
                    pt_mode = mode_elem[0].text
                    if pt_mode:
                        mode = pt_mode.lower()
                        
                        # Get submode for more specific transport type
                        if pt_mode.lower() == "rail":
                            rail_submode_elem = service[0].xpath('.//ojp:Mode/siri:RailSubmode', namespaces=cls.NAMESPACES)
                            if rail_submode_elem and rail_submode_elem[0].text:
                                submode = rail_submode_elem[0].text
                                # Map common rail submodes to more readable names
                                if submode == "regionalRail":
                                    mode = "regional_train"
                                elif submode == "suburbanRailway":
                                    mode = "s_bahn"
                                elif submode == "interregionalRail":
                                    mode = "intercity"
                                elif submode == "highSpeedRail":
                                    mode = "high_speed_rail"
                                else:
                                    mode = "train"
                        elif pt_mode.lower() == "bus":
                            bus_submode_elem = service[0].xpath('.//ojp:Mode/siri:BusSubmode', namespaces=cls.NAMESPACES)
                            if bus_submode_elem and bus_submode_elem[0].text:
                                submode = bus_submode_elem[0].text
                                # Map common bus submodes
                                if submode == "localBus":
                                    mode = "bus"
                                elif submode == "expressBus":
                                    mode = "express_bus"
                                elif submode == "nightBus":
                                    mode = "night_bus"
                                else:
                                    mode = "bus"
                        elif pt_mode.lower() == "tram":
                            mode = "tram"
                        elif pt_mode.lower() == "metro":
                            mode = "metro"
                        elif pt_mode.lower() == "funicular":
                            mode = "funicular"
                        elif pt_mode.lower() == "cableCar":
                            mode = "cable_car"
            
            return Leg(
                mode=mode,
                origin=origin,
                destination=destination,
                departure_time=departure_time,
                arrival_time=arrival_time,
                line_name=line_name,
                direction=direction
            )
            
        except Exception:
            return None
    
    @classmethod
    def _parse_continuous_leg(cls, leg_elem) -> Optional[Leg]:
        """Parse a continuous leg (walking, cycling, etc.)."""
        try:
            # Get origin and destination from TransferLeg
            transfer_leg = leg_elem.xpath('.//ojp:TransferLeg', namespaces=cls.NAMESPACES)
            if not transfer_leg:
                return None
            
            origin_elem = transfer_leg[0].xpath('.//ojp:LegStart', namespaces=cls.NAMESPACES)
            destination_elem = transfer_leg[0].xpath('.//ojp:LegEnd', namespaces=cls.NAMESPACES)
            
            origin = cls._parse_transfer_location(origin_elem[0]) if origin_elem else None
            destination = cls._parse_transfer_location(destination_elem[0]) if destination_elem else None
            
            # Get transfer type (walk, cycle, etc.)
            transfer_type_elem = transfer_leg[0].xpath('.//ojp:TransferType', namespaces=cls.NAMESPACES)
            mode = "walking"  # default
            if transfer_type_elem:
                mode_text = transfer_type_elem[0].text
                if mode_text:
                    mode = mode_text.lower()
            
            # Get duration from the Leg level or TransferLeg level
            duration_elem = leg_elem.xpath('.//ojp:Duration', namespaces=cls.NAMESPACES)
            if not duration_elem:
                duration_elem = transfer_leg[0].xpath('.//ojp:Duration', namespaces=cls.NAMESPACES)
            
            duration_minutes = None
            if duration_elem:
                duration_text = duration_elem[0].text
                if duration_text:
                    # Parse ISO 8601 duration (e.g., PT6M, PT1H30M)
                    duration_minutes = cls._parse_iso_duration(duration_text)
            
            return Leg(
                mode=mode,
                origin=origin or Location(name="Unknown", probability=None),
                destination=destination or Location(name="Unknown", probability=None),
                duration_minutes=duration_minutes
            )
            
        except Exception:
            return None
    
    @classmethod
    def _parse_transfer_leg(cls, leg_elem, transfer_leg_elem) -> Optional[Leg]:
        """Parse a transfer leg (walking, cycling, etc.) that's a direct child of Leg."""
        try:
            # Get origin and destination from LegStart and LegEnd
            origin_elem = transfer_leg_elem.xpath('./ojp:LegStart', namespaces=cls.NAMESPACES)
            destination_elem = transfer_leg_elem.xpath('./ojp:LegEnd', namespaces=cls.NAMESPACES)
            
            origin = cls._parse_transfer_location(origin_elem[0]) if origin_elem else None
            destination = cls._parse_transfer_location(destination_elem[0]) if destination_elem else None
            
            # Get transfer type (walk, cycle, etc.)
            transfer_type_elem = transfer_leg_elem.xpath('./ojp:TransferType', namespaces=cls.NAMESPACES)
            mode = "walking"  # default
            if transfer_type_elem:
                mode_text = transfer_type_elem[0].text
                if mode_text:
                    mode = mode_text.lower()
            
            # Get duration from the Leg level first, then TransferLeg level
            duration_elem = leg_elem.xpath('./ojp:Duration', namespaces=cls.NAMESPACES)
            if not duration_elem:
                duration_elem = transfer_leg_elem.xpath('./ojp:Duration', namespaces=cls.NAMESPACES)
            
            duration_minutes = None
            if duration_elem:
                duration_text = duration_elem[0].text
                if duration_text:
                    # Parse ISO 8601 duration (e.g., PT6M, PT1H30M)
                    duration_minutes = cls._parse_iso_duration(duration_text)
            
            return Leg(
                mode=mode,
                origin=origin or Location(name="Unknown", probability=None),
                destination=destination or Location(name="Unknown", probability=None),
                duration_minutes=duration_minutes
            )
            
        except Exception:
            return None
    
    @classmethod
    def _parse_transfer_location(cls, location_elem) -> Location:
        """Parse a location from a LegStart or LegEnd element in TransferLeg."""
        try:
            # Get location name from Name/Text or n/Text (both formats exist in the XML)
            name_elem = location_elem.xpath('.//ojp:Name/ojp:Text', namespaces=cls.NAMESPACES)
            if not name_elem:
                name_elem = location_elem.xpath('.//ojp:n/ojp:Text', namespaces=cls.NAMESPACES)
            
            name = name_elem[0].text if name_elem else "Unknown"
            
            # Get stop point reference for ID
            ref_elem = location_elem.xpath('.//siri:StopPointRef', namespaces=cls.NAMESPACES)
            location_id = ref_elem[0].text if ref_elem else None
            
            return Location(name=name, id=location_id, probability=None)
            
        except Exception:
            return Location(name="Unknown", probability=None)

    @classmethod
    def _parse_iso_duration(cls, duration_text: str) -> Optional[int]:
        """Parse ISO 8601 duration to minutes."""
        try:
            # Simple parsing for PT format (e.g., PT15M, PT1H30M, PT6M)
            if not duration_text.startswith('PT'):
                return None
            
            duration_text = duration_text[2:]  # Remove 'PT'
            minutes = 0
            
            # Parse hours
            if 'H' in duration_text:
                parts = duration_text.split('H')
                hours = int(parts[0])
                minutes += hours * 60
                duration_text = parts[1] if len(parts) > 1 else ''
            
            # Parse minutes
            if 'M' in duration_text:
                minutes_part = duration_text.replace('M', '')
                if minutes_part:
                    minutes += int(minutes_part)
            
            return minutes
            
        except (ValueError, IndexError):
            return None
    
    @classmethod
    def _parse_leg_board_alight(cls, location_elem) -> Location:
        """Parse a location from a LegBoard or LegAlight element."""
        try:
            # Get location name from StopPointName
            name_elem = location_elem.xpath('.//ojp:StopPointName/ojp:Text', namespaces=cls.NAMESPACES)
            name = name_elem[0].text if name_elem else "Unknown"
            
            # Get stop point reference for ID
            ref_elem = location_elem.xpath('.//siri:StopPointRef', namespaces=cls.NAMESPACES)
            location_id = ref_elem[0].text if ref_elem else None
            
            return Location(name=name, id=location_id, probability=None)
            
        except Exception:
            return Location(name="Unknown", probability=None)

    @classmethod
    def _parse_leg_location(cls, location_elem) -> Location:
        """Parse a location from a leg element."""
        try:
            # Get location name
            name_elem = location_elem.xpath('.//ojp:LocationName/ojp:Text', namespaces=cls.NAMESPACES)
            name = name_elem[0].text if name_elem else "Unknown"
            
            # Get coordinates
            coordinates = None
            coord_elem = location_elem.xpath('.//ojp:GeoPosition', namespaces=cls.NAMESPACES)
            if coord_elem:
                lon_elem = coord_elem[0].xpath('.//ojp:Longitude', namespaces=cls.NAMESPACES)
                lat_elem = coord_elem[0].xpath('.//ojp:Latitude', namespaces=cls.NAMESPACES)
                
                if lon_elem and lat_elem:
                    try:
                        coordinates = Coordinates(
                            longitude=float(lon_elem[0].text),
                            latitude=float(lat_elem[0].text)
                        )
                    except (ValueError, TypeError):
                        pass
            
            return Location(name=name, coordinates=coordinates, probability=None)
            
        except Exception:
            return Location(name="Unknown", probability=None)

    @classmethod
    def _parse_place_result(cls, place_elem) -> Optional[Location]:
        """Parse a place result from location information response."""
        try:
            # Navigate to the Place element
            place = place_elem.xpath('./ojp:Place', namespaces=cls.NAMESPACES)
            if not place:
                return None
            
            place = place[0]
            
            # Get location name from Name/Text
            name_elem = place.xpath('./ojp:Name/ojp:Text', namespaces=cls.NAMESPACES)
            name = name_elem[0].text if name_elem else None
            
            # Try to get name from StopPlace/StopPlaceName if Name is not available
            if not name:
                stop_name_elem = place.xpath('./ojp:StopPlace/ojp:StopPlaceName/ojp:Text', namespaces=cls.NAMESPACES)
                name = stop_name_elem[0].text if stop_name_elem else None
            
            if not name:
                return None
            
            # Get coordinates from GeoPosition
            coordinates = None
            coord_elem = place.xpath('./ojp:GeoPosition', namespaces=cls.NAMESPACES)
            if coord_elem:
                lon_elem = coord_elem[0].xpath('./siri:Longitude', namespaces=cls.NAMESPACES)
                lat_elem = coord_elem[0].xpath('./siri:Latitude', namespaces=cls.NAMESPACES)
                
                if lon_elem and lat_elem:
                    try:
                        coordinates = Coordinates(
                            longitude=float(lon_elem[0].text),
                            latitude=float(lat_elem[0].text)
                        )
                    except (ValueError, TypeError):
                        pass
            
            # Get location ID from StopPlaceRef
            location_id = None
            id_elem = place.xpath('./ojp:StopPlace/ojp:StopPlaceRef', namespaces=cls.NAMESPACES)
            if id_elem:
                location_id = id_elem[0].text
            
            # Get probability
            probability = None
            prob_elem = place_elem.xpath('./ojp:Probability', namespaces=cls.NAMESPACES)
            if prob_elem:
                try:
                    probability = float(prob_elem[0].text)
                except (ValueError, TypeError):
                    pass
            
            return Location(
                id=location_id,
                name=name,
                coordinates=coordinates,
                type="stop",
                probability=probability
            )
            
        except Exception:
            return None
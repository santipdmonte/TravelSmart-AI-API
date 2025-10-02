import os
from typing import Optional, TypedDict, Any
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class MapboxContext(TypedDict, total=False):
    """Context information from Mapbox response"""
    id: str
    mapbox_id: str
    text: str
    wikidata: Optional[str]
    short_code: Optional[str]


class MapboxProperties(TypedDict, total=False):
    """Properties object from Mapbox geocoding response"""
    mapbox_id: str
    feature_type: str
    full_address: Optional[str]
    name: Optional[str]
    name_preferred: Optional[str]
    coordinates: dict[str, float]
    place_formatted: Optional[str]
    context: Optional[dict[str, MapboxContext]]
    bbox: Optional[list[float]]
    match_code: Optional[dict[str, Any]]


class MapboxGeometry(TypedDict):
    """Geometry object from Mapbox geocoding response"""
    type: str
    coordinates: list[float]  # [longitude, latitude]


class MapboxFeature(TypedDict):
    """Individual feature from Mapbox geocoding response"""
    type: str
    id: str
    geometry: MapboxGeometry
    properties: MapboxProperties


class MapboxGeocodingResponse(TypedDict):
    """Complete Mapbox geocoding response"""
    type: str
    features: list[MapboxFeature]
    attribution: str


class AttractionCoordinates(TypedDict):
    """Simplified coordinates response for an attraction"""
    attraction: str
    latitude: float
    longitude: float
    full_address: str
    place_name: str
    city: Optional[str]
    region: Optional[str]
    country: Optional[str]
    country_code: Optional[str]


class GeocodingInput(BaseModel):
    """Input schema for geocoding tool"""
    search_text: str = Field(description='The location or address to geocode (e.g., "Eiffel Tower, Paris" or "Times Square, New York")')
    country: Optional[str] = Field(None, description='ISO 3166-1 alpha-2 country code to limit results (e.g., "US", "FR", "ES")')
    language: Optional[str] = Field("en", description='Language for results (ISO 639-1 code, e.g., "en", "es", "fr")')
    limit: Optional[int] = Field(1, description='Maximum number of results to return (1-10)')
    proximity: Optional[str] = Field(None, description='Bias results to this location, format: "longitude,latitude"')


class GeocodingInputSchema(BaseModel):
    """Wrapper schema for geocoding input"""
    params: GeocodingInput


def geocode_location(params: GeocodingInput) -> dict[str, Any] | str:
    """
    Geocode a location using the Mapbox Geocoding API.
    
    Converts location text (like "Eiffel Tower, Paris") into geographic coordinates
    and detailed location information.
    
    Args:
        params: GeocodingInput with search text and optional filters
    
    Returns:
        dict: Geocoding results with coordinates and location details, or error string
    """
    
    access_token = os.environ.get('MAPBOX_ACCESS_TOKEN')
    
    if not access_token:
        return "Error: MAPBOX_ACCESS_TOKEN not found in environment variables"
    
    # Build request URL
    base_url = "https://api.mapbox.com/search/geocode/v6/forward"
    
    # Build query parameters
    query_params = {
        'q': params.search_text,
        'access_token': access_token,
        'language': params.language or 'en',
        'limit': params.limit or 1,
    }
    
    # Add optional parameters
    if params.country:
        query_params['country'] = params.country
    
    if params.proximity:
        query_params['proximity'] = params.proximity
    
    try:
        response = requests.get(base_url, params=query_params, timeout=10)
        response.raise_for_status()
        
        data: MapboxGeocodingResponse = response.json()
        
        if not data.get('features') or len(data['features']) == 0:
            return f"No results found for: {params.search_text}"
        
        # Extract the first/best result
        feature = data['features'][0]
        geometry = feature['geometry']
        properties = feature['properties']
        
        # Extract context information (city, region, country, etc.)
        context = properties.get('context', {})
        
        # Helper function to get context value by type
        def get_context_value(feature_type: str) -> Optional[str]:
            for key, value in context.items():
                if key.startswith(feature_type):
                    return value.get('name') or value.get('text')
            return None
        
        result: AttractionCoordinates = {
            'attraction': params.search_text,
            'latitude': geometry['coordinates'][1],
            'longitude': geometry['coordinates'][0],
            'full_address': properties.get('full_address') or properties.get('place_formatted', ''),
            'place_name': properties.get('name_preferred') or properties.get('name', ''),
            'city': get_context_value('place') or get_context_value('locality'),
            'region': get_context_value('region'),
            'country': get_context_value('country'),
            'country_code': None  # Extract from context if needed
        }
        
        # Try to get country code from context
        for key, value in context.items():
            if key.startswith('country'):
                result['country_code'] = value.get('short_code')
                break
        
        return result
        
    except requests.exceptions.Timeout:
        return f"Error: Request timeout while geocoding {params.search_text}"
    except requests.exceptions.RequestException as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def batch_geocode_attractions(attractions: list[str], country: Optional[str] = None) -> dict[str, dict]:
    """
    Geocode multiple attractions/locations at once.
    
    Args:
        attractions: List of location names to geocode
        country: Optional ISO 3166-1 alpha-2 country code to limit results
    
    Returns:
        dict[str, dict]: Dictionary with attraction names as keys and geocoding data or error info as values
        Example:
        {
            "Torre Eiffel": {
                "success": True,
                "attraction": "Torre Eiffel",
                "latitude": 48.858,
                "longitude": 2.294,
                "full_address": "...",
                "city": "Paris",
                "country": "France",
                ...
            },
            "Invalid Place": {
                "success": False,
                "error": "No results found for: Invalid Place"
            }
        }
    """
    results = {}
    
    for attraction in attractions:
        input_params = GeocodingInput(
            search_text=attraction,
            country=country,
            limit=1
        )
        result = geocode_location(input_params)
        
        # Process result into consistent format
        if isinstance(result, dict):
            # Success - add success flag
            results[attraction] = {
                **result,
                "success": True
            }
        else:
            # Error - create error object
            results[attraction] = {
                "success": False,
                "error": result
            }
    
    return results


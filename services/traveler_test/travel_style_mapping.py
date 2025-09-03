"""
Mapping between Traveler Types and default Travel Style slugs used in the frontend.

These slugs must match the TRAVEL_STYLES defined in the frontend create page:
['cultural', 'relaxing', 'adventurous', 'romantic', 'adrenaline', 'gastronomic', 'festive']
"""

from typing import Dict, List

# Default mapping. Adjust if product requirements change.
TRAVELER_TYPE_STYLE_MAP: Dict[str, List[str]] = {
    "Aventurero": ["adventurous", "adrenaline"],
    "Explorador Cultural": ["cultural", "gastronomic"],
    "Viajero Relajado": ["relaxing", "romantic"],
    "Gourmet": ["gastronomic"],
    "Social y Nocturno": ["festive"],
    "Romántico": ["romantic", "relaxing"],
}

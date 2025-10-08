"""
Wikipedia tool for extracting information and images about locations and attractions.

This tool uses the Wikipedia API to search for articles and extract:
- Summaries and full content
- Images and their URLs
- Geographic coordinates
- Related links and categories
"""

import requests
from typing import Optional, TypedDict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool


# User-Agent header requerido por la API de Wikipedia
# Según la política de etiqueta de MediaWiki: https://www.mediawiki.org/wiki/API:Etiquette
HEADERS = {
    'User-Agent': 'TravelSmart-AI/1.0 (https://github.com/travelsmart; contact@travelsmart.com) Python/requests'
}


class WikipediaImage(TypedDict, total=False):
    """Image information from Wikipedia"""
    url: str
    title: str
    description: Optional[str]
    width: Optional[int]
    height: Optional[int]


class WikipediaCoordinates(TypedDict, total=False):
    """Geographic coordinates from Wikipedia"""
    latitude: float
    longitude: float


class WikipediaPageInfo(TypedDict):
    """Complete information from a Wikipedia page"""
    title: str
    page_id: int
    url: str
    summary: str
    extract: str
    images: list[WikipediaImage]
    coordinates: Optional[WikipediaCoordinates]
    categories: list[str]
    language: str


class WikipediaSearchResult(TypedDict):
    """Search result from Wikipedia"""
    page_id: int
    title: str
    snippet: str


class WikipediaInput(BaseModel):
    """Input schema for Wikipedia search"""
    query: str = Field(description='Search query for Wikipedia (e.g., "Eiffel Tower", "Sagrada Familia")')
    language: Optional[str] = Field("en", description='Language code (e.g., "en", "es", "fr", "de")')
    sentences: Optional[int] = Field(3, description='Number of sentences in summary (1-10)')
    auto_suggest: Optional[bool] = Field(True, description='Enable auto-suggest for better results')


class WikipediaInputSchema(BaseModel):
    """Wrapper schema for Wikipedia input"""
    params: WikipediaInput


def _get_wikipedia_api_url(language: str = "en") -> str:
    """Get the Wikipedia API URL for a specific language"""
    return f"https://{language}.wikipedia.org/w/api.php"


def _search_wikipedia(query: str, language: str = "en", limit: int = 5) -> list[WikipediaSearchResult]:
    """
    Search Wikipedia for pages matching the query.
    
    Args:
        query: Search query
        language: Language code
        limit: Maximum number of results
    
    Returns:
        List of search results
    """
    url = _get_wikipedia_api_url(language)
    
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': query,
        'srlimit': limit,
        'format': 'json',
        'utf8': 1
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get('query', {}).get('search', []):
            results.append(WikipediaSearchResult(
                page_id=item['pageid'],
                title=item['title'],
                snippet=item['snippet']
            ))
        
        return results
    
    except Exception as e:
        print(f"Error searching Wikipedia: {e}")
        return []


def _get_page_info(page_id: int, language: str = "en", sentences: int = 3) -> Optional[WikipediaPageInfo]:
    """
    Get detailed information about a Wikipedia page.
    
    Args:
        page_id: Wikipedia page ID
        language: Language code
        sentences: Number of sentences for summary
    
    Returns:
        Complete page information or None if error
    """
    url = _get_wikipedia_api_url(language)
    
    # Get page content, images, and coordinates
    params = {
        'action': 'query',
        'pageids': page_id,
        'prop': 'extracts|pageimages|coordinates|categories|info',
        'exintro': True,
        'exsentences': sentences,
        'explaintext': True,
        'piprop': 'original|name',
        'pilimit': 10,
        'inprop': 'url',
        'format': 'json',
        'utf8': 1
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        page_data = data.get('query', {}).get('pages', {}).get(str(page_id), {})
        
        if not page_data or 'missing' in page_data:
            return None
        
        # Extract basic info
        title = page_data.get('title', '')
        summary = page_data.get('extract', '')
        page_url = page_data.get('fullurl', f"https://{language}.wikipedia.org/wiki/{title.replace(' ', '_')}")
        
        # Extract coordinates if available
        coordinates = None
        if 'coordinates' in page_data and page_data['coordinates']:
            coord = page_data['coordinates'][0]
            coordinates = WikipediaCoordinates(
                latitude=coord.get('lat', 0.0),
                longitude=coord.get('lon', 0.0)
            )
        
        # Extract categories
        categories = []
        if 'categories' in page_data:
            categories = [cat['title'].replace('Category:', '') for cat in page_data.get('categories', [])]
        
        # Get images from the page
        images = _get_page_images(page_id, language)
        
        # Get full extract (not just intro)
        full_extract = _get_full_extract(page_id, language)
        
        return WikipediaPageInfo(
            title=title,
            page_id=page_id,
            url=page_url,
            summary=summary,
            extract=full_extract or summary,
            images=images,
            coordinates=coordinates,
            categories=categories[:10],  # Limit categories
            language=language
        )
    
    except Exception as e:
        print(f"Error getting page info: {e}")
        return None


def _get_page_images(page_id: int, language: str = "en", limit: int = 5) -> list[WikipediaImage]:
    """
    Get images from a Wikipedia page.
    
    Args:
        page_id: Wikipedia page ID
        language: Language code
        limit: Maximum number of images
    
    Returns:
        List of images with URLs and metadata
    """
    url = _get_wikipedia_api_url(language)
    
    # First, get image titles
    params = {
        'action': 'query',
        'pageids': page_id,
        'prop': 'images',
        'imlimit': limit + 5,  # Get extra to filter out icons
        'format': 'json',
        'utf8': 1
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        page_data = data.get('query', {}).get('pages', {}).get(str(page_id), {})
        image_titles = [img['title'] for img in page_data.get('images', [])]
        
        if not image_titles:
            return []
        
        # Get image URLs and info
        images = []
        for i in range(0, len(image_titles), 50):  # API allows up to 50 titles per request
            batch = image_titles[i:i+50]
            
            params = {
                'action': 'query',
                'titles': '|'.join(batch),
                'prop': 'imageinfo',
                'iiprop': 'url|size|extmetadata',
                'format': 'json',
                'utf8': 1
            }
            
            response = requests.get(url, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for page in data.get('query', {}).get('pages', {}).values():
                if 'imageinfo' not in page:
                    continue
                
                image_info = page['imageinfo'][0]
                title = page.get('title', '').replace('File:', '')
                
                # Filter out common icons and small images
                if any(skip in title.lower() for skip in ['icon', 'logo', 'symbol', 'flag', '.svg']):
                    continue
                
                if image_info.get('width', 0) < 200 or image_info.get('height', 0) < 200:
                    continue
                
                # Extract description from metadata
                description = None
                extmetadata = image_info.get('extmetadata', {})
                if 'ImageDescription' in extmetadata:
                    description = extmetadata['ImageDescription'].get('value', '')
                
                images.append(WikipediaImage(
                    url=image_info.get('url', ''),
                    title=title,
                    description=description,
                    width=image_info.get('width'),
                    height=image_info.get('height')
                ))
                
                if len(images) >= limit:
                    break
            
            if len(images) >= limit:
                break
        
        return images[:limit]
    
    except Exception as e:
        print(f"Error getting images: {e}")
        return []


def _get_full_extract(page_id: int, language: str = "en") -> Optional[str]:
    """
    Get the full text extract from a Wikipedia page.
    
    Args:
        page_id: Wikipedia page ID
        language: Language code
    
    Returns:
        Full page text or None
    """
    url = _get_wikipedia_api_url(language)
    
    params = {
        'action': 'query',
        'pageids': page_id,
        'prop': 'extracts',
        'explaintext': True,
        'format': 'json',
        'utf8': 1
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        page_data = data.get('query', {}).get('pages', {}).get(str(page_id), {})
        return page_data.get('extract')
    
    except Exception as e:
        print(f"Error getting full extract: {e}")
        return None


def get_wikipedia_info(params: WikipediaInput) -> WikipediaPageInfo | str:
    """
    Search Wikipedia and get detailed information including text and images.
    
    This tool searches Wikipedia for the given query and returns comprehensive
    information including:
    - Page title and URL
    - Summary and full text extract
    - Images with URLs
    - Geographic coordinates (if available)
    - Categories
    
    Args:
        params: WikipediaInput with query and optional language/settings
    
    Returns:
        WikipediaPageInfo: Complete page information with images and text
        str: Error message if search fails
    
    Example:
        >>> params = WikipediaInput(query="Eiffel Tower", language="en")
        >>> result = get_wikipedia_info({"params": params})
    """
    
    # Search for the page
    search_results = _search_wikipedia(
        query=params.query,
        language=params.language or "en",
        limit=1
    )
    
    if not search_results:
        return f"No Wikipedia results found for: {params.query}"
    
    # Get detailed info for the first result
    page_info = _get_page_info(
        page_id=search_results[0]['page_id'],
        language=params.language or "en",
        sentences=params.sentences or 3
    )
    
    if not page_info:
        return f"Could not retrieve information for: {search_results[0]['title']}"
    
    return page_info


def search_wikipedia_pages(query: str, language: str = "en", limit: int = 5) -> list[WikipediaSearchResult] | str:
    """
    Search Wikipedia and return multiple matching pages.
    
    Args:
        query: Search query
        language: Language code (default: "en")
        limit: Maximum number of results (default: 5)
    
    Returns:
        list[WikipediaSearchResult]: List of search results
        str: Error message if search fails
    
    Example:
        >>> results = search_wikipedia_pages({
        ...     "query": "Paris monuments",
        ...     "language": "en",
        ...     "limit": 5
        ... })
    """
    
    results = _search_wikipedia(query, language, limit)
    
    if not results:
        return f"No Wikipedia results found for: {query}"
    
    return results


def get_wikipedia_images(query: str, language: str = "en", max_images: int = 5) -> list[WikipediaImage] | str:
    """
    Get images from a Wikipedia page.
    
    Args:
        query: Search query for the Wikipedia page
        language: Language code (default: "en")
        max_images: Maximum number of images to return (default: 5)
    
    Returns:
        list[WikipediaImage]: List of images with URLs and metadata
        str: Error message if search fails
    
    Example:
        >>> images = get_wikipedia_images({
        ...     "query": "Sagrada Familia",
        ...     "language": "es",
        ...     "max_images": 3
        ... })
    """
    
    # Search for the page
    search_results = _search_wikipedia(query, language, limit=1)
    
    if not search_results:
        return f"No Wikipedia page found for: {query}"
    
    # Get images
    images = _get_page_images(
        page_id=search_results[0]['page_id'],
        language=language,
        limit=max_images
    )
    
    if not images:
        return f"No images found for: {search_results[0]['title']}"
    
    return images


def batch_get_wikipedia_images(
    queries: list[str], 
    language: str = "en", 
    max_images_per_query: int = 3
) -> dict[str, dict]:
    """
    Get images from multiple Wikipedia pages in batch.
    
    This tool is optimized for processing multiple locations/attractions at once,
    such as getting images for all attractions in a travel itinerary.
    
    Args:
        queries: List of search queries (e.g., ["Eiffel Tower", "Louvre Museum", "Notre-Dame"])
        language: Language code (default: "en")
        max_images_per_query: Maximum number of images per query (default: 3)
    
    Returns:
        dict[str, dict]: Dictionary with query names as keys and image data or error info as values
        Example:
        {
            "Eiffel Tower": {
                "success": True,
                "title": "Eiffel Tower",
                "images": [
                    {"url": "...", "title": "...", "description": "..."},
                    {"url": "...", "title": "...", "description": "..."}
                ]
            },
            "Invalid Place": {
                "success": False,
                "error": "No Wikipedia page found for: Invalid Place"
            }
        }
    
    Example:
        >>> results = batch_get_wikipedia_images(
        ...     queries=["Eiffel Tower", "Louvre Museum", "Arc de Triomphe"],
        ...     language="en",
        ...     max_images_per_query=2
        ... )
        >>> for attraction, data in results.items():
        ...     if data['success']:
        ...         print(f"{attraction} ({data['title']}): {len(data['images'])} images")
    """
    
    results = {}
    
    for query in queries:
        # Search for the page
        search_results = _search_wikipedia(query, language, limit=1)
        
        if not search_results:
            results[query] = {
                "success": False,
                "title": "",
                "images": [],
                "error": f"No Wikipedia page found for: {query}"
            }
            continue
        
        # Get images
        images = _get_page_images(
            page_id=search_results[0]['page_id'],
            language=language,
            limit=max_images_per_query
        )
        
        results[query] = {
            # "success": True,
            # "title": search_results[0]['title'],
            "images": images,
            # "error": None
        }
    
    return results


def batch_get_wikipedia_info(
    queries: list[str],
    language: str = "en",
    sentences: int = 2,
    max_images: int = 3
) -> dict[str, WikipediaPageInfo]:
    """
    Get complete Wikipedia information for multiple topics in batch.
    
    This tool retrieves full page information (text, images, coordinates) for
    multiple queries at once. Ideal for enriching entire travel itineraries.
    
    Args:
        queries: List of search queries (e.g., ["Paris", "Rome", "Barcelona"])
        language: Language code (default: "en")
        sentences: Number of sentences in summary (default: 2)
        max_images: Maximum images per query (default: 3)
    
    Returns:
        dict[str, WikipediaPageInfo]: Complete information for each query, keyed by query
    
    Example:
        >>> results = batch_get_wikipedia_info({
        ...     "queries": ["Sagrada Familia", "Park Güell", "Camp Nou"],
        ...     "language": "es",
        ...     "sentences": 2
        ... })
        >>> for result in results:
        ...     if result['success']:
        ...         info = result['page_info']
        ...         print(f"{info['title']}: {info['summary'][:100]}...")
    """
    
    results = {}
    
    for query in queries:
        # Search for the page
        search_results = _search_wikipedia(query, language, limit=1)
        
        if not search_results:
            results[query] = WikipediaPageInfo(
                query=query,
                page_info=None,
                success=False,
                error=f"No Wikipedia page found for: {query}"
            )
            continue
        
        # Get detailed page info
        page_info = _get_page_info(
            page_id=search_results[0]['page_id'],
            language=language,
            sentences=sentences
        )
        
        if not page_info:
            results[query] = WikipediaPageInfo(
                query=query,
                page_info=None,
                success=False,
                error=f"Could not retrieve information for: {search_results[0]['title']}"
            )
            continue
        
        # Limit images to max_images
        if page_info['images'] and len(page_info['images']) > max_images:
            page_info['images'] = page_info['images'][:max_images]
        
        results[query] = WikipediaPageInfo(
            query=query,
            page_info=page_info,
            success=True,
            error=None
        )
    
    return results




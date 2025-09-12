from typing import Dict, List, Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
import json
import random
import time
import os


def _detect_provider(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "airbnb." in host:
        return "AIRBNB"
    if "booking." in host:
        return "BOOKING"
    if "expedia." in host:
        return "EXPEDIA"
    return "OTHER"


def scrape_accommodation(url: str) -> Dict[str, Optional[str] | List[str]]:
    provider = _detect_provider(url)
    if provider == "AIRBNB":
        return _scrape_airbnb(url)
    if provider == "BOOKING":
        return _scrape_booking(url)
    # if provider == "EXPEDIA":
    #     return _scrape_expedia(url)
    # Fallback
    return {"provider": provider, "title": None, "description": None, "images": []}


def _scrape_airbnb(url: str) -> Dict[str, Optional[str] | List[str]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    with httpx.Client(follow_redirects=True, timeout=20) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    # Title and description via meta tags or JSON-LD
    title = _first_non_empty(
        soup.select_one('meta[property="og:title"]'),
        soup.select_one('meta[name="twitter:title"]'),
    )
    title_text = title.get("content") if title else None

    description_el = _first_non_empty(
        soup.select_one('meta[property="og:description"]'),
        soup.select_one('meta[name="description"]'),
        soup.select_one('meta[name="twitter:description"]'),
    )
    description_text = description_el.get("content") if description_el else None

    images: List[str] = []

    # Try JSON-LD blocks (Airbnb often embeds listing data)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            imgs = _extract_images_from_jsonld(data)
            if imgs:
                images.extend(imgs)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    imgs = _extract_images_from_jsonld(item)
                    if imgs:
                        images.extend(imgs)

    # Fallback to OpenGraph image(s)
    if not images:
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image and og_image.get("content"):
            images.append(og_image.get("content"))

    # Deduplicate and cap to 5
    deduped = []
    for u in images:
        if isinstance(u, str) and u not in deduped:
            deduped.append(u)
    images_out = deduped[:5]

    return {
        "provider": "AIRBNB",
        "title": title_text,
        "description": description_text,
        "images": images_out,
    }


def _scrape_booking(url: str) -> Dict[str, Optional[str] | List[str]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    with httpx.Client(follow_redirects=True, timeout=20) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    title = _first_non_empty(
        soup.select_one('meta[property="og:title"]'),
        soup.select_one('meta[name="twitter:title"]'),
        soup.select_one('title'),
    )
    title_text = (title.get("content") if title and title.name == "meta" else title.text.strip() if title else None)

    description_el = _first_non_empty(
        soup.select_one('meta[property="og:description"]'),
        soup.select_one('meta[name="description"]'),
        soup.select_one('meta[name="twitter:description"]'),
    )
    description_text = description_el.get("content") if description_el else None

    images: List[str] = []

    # JSON-LD images if present
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            images.extend(_extract_images_from_jsonld(data))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    images.extend(_extract_images_from_jsonld(item))

    if not images:
        # Booking often has og:image
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image and og_image.get("content"):
            images.append(og_image.get("content"))

    images_out = _dedupe_cap(images, 5)

    return {
        "provider": "BOOKING",
        "title": title_text,
        "description": description_text,
        "images": images_out,
    }



def _extract_images_from_jsonld(data: dict) -> List[str]:
    images: List[str] = []
    if "image" in data:
        image_val = data["image"]
        if isinstance(image_val, str):
            images.append(image_val)
        elif isinstance(image_val, list):
            images.extend([u for u in image_val if isinstance(u, str)])
        elif isinstance(image_val, dict):
            # Some formats use @type ImageObject
            url = image_val.get("url")
            if isinstance(url, str):
                images.append(url)
    return images


def _first_non_empty(*elements):
    for el in elements:
        if el is not None:
            return el
    return None


def _dedupe_cap(items: List[str], limit: int) -> List[str]:
    seen = set()
    out: List[str] = []
    for u in items:
        if isinstance(u, str) and u not in seen:
            seen.add(u)
            out.append(u)
            if len(out) >= limit:
                break
    return out



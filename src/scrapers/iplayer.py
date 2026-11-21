"""
BBC iPlayer scraper module.
This module handles fetching and parsing movie data from BBC iPlayer.
"""

import json
import re
import requests
import logging
from typing import List, Dict, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class IPlayerScraper:
    """Class to handle scraping of BBC iPlayer movie data."""
    
    def __init__(self):
        """Initialize the iPlayer scraper."""
        self.base_url = "https://www.bbc.co.uk"
        self.films_url = "https://www.bbc.co.uk/iplayer/browse/films"
        # The JSON endpoint the films page itself uses to load more of each carousel
        self.collection_url = "https://www.bbc.co.uk/wc-data/container/simple-promo-collection"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        self.logger = logging.getLogger(__name__)
    
    def get_current_movies(self) -> List[Dict[str, Any]]:
        """
        Fetch the current list of movies available on BBC iPlayer
        Returns a list of dictionaries containing movie information
        
        iPlayer has no A-Z of films any more, only themed carousels on the
        films page, so we collect every film from every carousel.
        """
        self.logger.info("Fetching current movies from iPlayer...")
        movies = {}
        try:
            response = requests.get(self.films_url, headers=self.headers)
            response.raise_for_status()
            urns = self._collection_urns(response.text)
            self.logger.info(f"Found {len(urns)} film collections")
            
            for urn in urns:
                for promo in self._collection_promos(urn):
                    if promo['episodeId'] not in movies:
                        movies[promo['episodeId']] = self._parse_movie_data(
                            promo['headline'],
                            self.base_url + promo['url'],
                            promo.get('description'),
                            (promo.get('image') or {}).get('src'),
                        )
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            self.logger.error(f"Error fetching movies from iPlayer: {str(e)}")

        self.logger.info(f"Found total of {len(movies)} movies on iPlayer")
        return list(movies.values())
    
    def _collection_urns(self, html: str) -> List[str]:
        """Find the id of every film carousel in the page's embedded data."""
        match = re.search(r'window\.__INITIAL_DATA__=(".*?");?\s*</script>', html, re.S)
        if not match:
            raise ValueError("No __INITIAL_DATA__ found on films page")
        components = json.loads(json.loads(match.group(1)))['data'].values()
        return [c['data']['urn'] for c in components
                if isinstance(c.get('data'), dict) and 'total' in c['data'] and 'urn' in c['data']]
    
    def _collection_promos(self, urn: str):
        """Yield every promo in a carousel, page by page."""
        seen = set()
        page = 1
        while True:
            params = {
                'dataType': 'contentCollectionData',
                'home': 'iplayer',
                'isUk': 'true',
                'language': 'en-GB',
                'enableContinuousScroll': 'true',
                'urn': urn,
                'currentCarouselPage': page,
            }
            response = requests.get(self.collection_url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            new = [p for p in data['promos'] if p.get('episodeId') and p['episodeId'] not in seen]
            # Past the last page iPlayer repeats it rather than returning nothing
            if not new:
                return
            seen.update(p['episodeId'] for p in new)
            yield from new
            if len(seen) >= data['total']:
                return
            
            page += 1
            # Add a small delay to be nice to the server
            time.sleep(1)
    
    def _parse_movie_data(self, title, url, description, thumbnail):
        """Parse the movie data into a standardized format."""
        return {
            'title': title,
            'url': url,
            'description': description,
            'thumbnail': thumbnail
        }
    
    def _format_duration(self, seconds: int) -> str:
        """
        Format duration in seconds to a human-readable string.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string (e.g., "2h 30m")
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m" 
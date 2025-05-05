"""
IMDB scraper module using the OMDb API.
This module handles fetching movie data from IMDB via the OMDb API.
"""

import requests
import logging
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class IMDBScraper:
    """Class to handle fetching IMDB data via OMDb API."""
    
    def __init__(self):
        """Initialize the IMDB scraper."""
        load_dotenv()
        self.api_key = os.getenv('OMDB_API_KEY')
        if not self.api_key:
            raise ValueError("OMDB_API_KEY environment variable is required")
            
        self.base_url = "https://www.omdbapi.com/"
        self.logger = logging.getLogger(__name__)
        
        # Set up session with retries
        self.session = requests.Session()
        retries = Retry(
            total=3,  # number of retries
            backoff_factor=0.5,  # wait 0.5, 1, 2 seconds between retries
            status_forcelist=[500, 502, 503, 504],  # retry on these status codes
            allowed_methods=["GET"]
        )
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def get_movie_data(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Fetch movie data from IMDB using the OMDb API.
        
        Args:
            title: The title of the movie to search for
            
        Returns:
            Dictionary containing movie data (rating, review count, genres) or None if not found
        """
        try:
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)  # Wait 0.5 seconds between requests
            
            # Search for the exact movie
            params = {
                'apikey': self.api_key,
                't': title,  # search by title
                'type': 'movie',
                'r': 'json'  # get JSON response
            }
            
            self.logger.debug(f"Searching OMDb API for: {title}")
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 401:
                self.logger.error("Invalid API key or API key not activated")
                return None
                
            response.raise_for_status()
            data = response.json()
            
            if data.get('Response') == 'False':
                self.logger.warning(f"No IMDB results found for: {title}")
                return None
                
            # Extract the data we need
            try:
                imdb_rating = float(data.get('imdbRating', 0))
                if imdb_rating == 0:
                    imdb_rating = None
            except (ValueError, TypeError):
                imdb_rating = None
                
            try:
                review_count = int(data.get('imdbVotes', '0').replace(',', ''))
                if review_count == 0:
                    review_count = None
            except (ValueError, TypeError):
                review_count = None
                
            genres = [genre.strip() for genre in data.get('Genre', '').split(',') if genre.strip()]
            imdb_id = data.get('imdbID')
            imdb_url = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else None
            
            movie_data = {
                'rating': imdb_rating,
                'review_count': review_count,
                'genres': genres,
                'imdb_url': imdb_url,
                'year': data.get('Year')
            }
            
            self.logger.debug(f"Found IMDB data for {title}: {movie_data}")
            return movie_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching data from OMDb API for {title}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing OMDb API data for {title}: {str(e)}")
            return None 
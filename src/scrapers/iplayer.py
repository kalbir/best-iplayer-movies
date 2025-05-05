"""
BBC iPlayer scraper module.
This module handles fetching and parsing movie data from BBC iPlayer.
"""

import requests
from bs4 import BeautifulSoup
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
        self.movies_url = "https://www.bbc.co.uk/iplayer/categories/films/a-z"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        self.logger = logging.getLogger(__name__)
    
    def get_current_movies(self) -> List[Dict[str, Any]]:
        """
        Fetch the current list of movies available on BBC iPlayer
        Returns a list of dictionaries containing movie information
        """
        self.logger.info("Fetching current movies from iPlayer...")
        movies = []
        page = 1
        total_pages = None

        while True:
            try:
                # Construct URL with page parameter
                url = f"{self.movies_url}?page={page}"
                self.logger.info(f"Fetching page {page}...")
                
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                self.logger.debug(f"Response status code: {response.status_code}")
                
                soup = BeautifulSoup(response.text, 'html.parser')
                self.logger.debug("Successfully parsed HTML")
                
                # Find all movie items in the A-Z listing
                movie_items = soup.find_all('a', class_='content-item-root')
                self.logger.debug(f"Found {len(movie_items)} movie items on page {page}")

                if not movie_items:
                    self.logger.info("No more movies found, stopping pagination")
                    break

                for item in movie_items:
                    try:
                        # Extract movie details
                        title = item.find('div', class_='content-item-root__meta').text.strip()
                        url = self.base_url + item['href']
                        
                        # Extract description from aria-label
                        description = item.get('aria-label', '').split('. Description: ')[-1].split('. Duration:')[0]
                        
                        # Extract thumbnail
                        img_tag = item.find('img', class_='rs-image__img')
                        thumbnail = None
                        if img_tag and 'srcSet' in img_tag.attrs:
                            thumbnail = img_tag['srcSet'].split(' ')[0]

                        if title:  # Only add movies with titles
                            movie_data = self._parse_movie_data(title, url, description, thumbnail)
                            movies.append(movie_data)
                            self.logger.debug(f"Added movie: {title}")
                    except Exception as e:
                        self.logger.error(f"Error parsing movie item: {str(e)}")
                        continue

                # Check pagination
                pagination_list = soup.find('ol', class_='pagination__list')
                if pagination_list:
                    # Find all page numbers
                    page_numbers = []
                    for a in pagination_list.find_all('a', class_='button--numeral'):
                        try:
                            page_num = int(a.text.strip())
                            page_numbers.append(page_num)
                        except (ValueError, TypeError):
                            continue
                    
                    if page_numbers:
                        # Get the last page number
                        last_page = max(page_numbers)
                        if total_pages is None:
                            total_pages = last_page
                            self.logger.info(f"Total pages found: {total_pages}")
                    
                    # Check if we've reached the last page
                    if page >= (total_pages or float('inf')):
                        self.logger.info("Reached last page, stopping pagination")
                        break
                else:
                    self.logger.info("No pagination found, stopping after first page")
                    break

                page += 1
                # Add a small delay to be nice to the server
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error fetching movies from iPlayer: {str(e)}")
                break

        self.logger.info(f"Found total of {len(movies)} movies on iPlayer across {page} pages")
        return movies
    
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
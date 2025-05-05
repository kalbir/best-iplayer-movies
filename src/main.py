#!/usr/bin/env python3
"""
Main entry point for the Best iPlayer Movies project.
This script orchestrates the scraping, processing, and webpage generation.
"""

import logging
from pathlib import Path
from datetime import datetime
from scrapers.iplayer import IPlayerScraper
from scrapers.imdb import IMDBScraper
from jinja2 import Environment, FileSystemLoader
import os
import concurrent.futures
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_html(movies):
    """Generate HTML output using Jinja2 template."""
    # Filter out movies without IMDB ratings
    rated_movies = [movie for movie in movies if movie['imdb_data']['rating'] is not None]
    
    # Sort movies by rating
    sorted_movies = sorted(
        rated_movies,
        key=lambda x: float(x['imdb_data']['rating']),
        reverse=True
    )
    
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('src/templates'))
    template = env.get_template('movies.html')
    
    # Render template
    html_output = template.render(
        movies=sorted_movies,
        last_updated=datetime.now().strftime("%d %B %Y")
    )
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Write to file
    output_path = 'output/movies.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    return output_path

def fetch_imdb_data(movie: Dict[str, Any], imdb_scraper: IMDBScraper) -> Dict[str, Any]:
    """Fetch IMDB data for a single movie."""
    logger.debug(f"Fetching IMDB data for: {movie['title']}")
    imdb_data = imdb_scraper.get_movie_data(movie['title'])
    if imdb_data:
        logger.debug(f"Enriched movie data for: {movie['title']}")
        return {**movie, 'imdb_data': imdb_data}
    else:
        logger.warning(f"Could not find IMDB data for: {movie['title']}")
        return {
            **movie,
            'imdb_data': {
                'rating': None,
                'review_count': None,
                'genres': [],
                'imdb_url': None,
                'year': None
            }
        }

def main():
    """Main function to run the scrapers and generate output."""
    logger.info("Starting Best iPlayer Movies scraper")
    
    # Initialize scrapers
    iplayer_scraper = IPlayerScraper()
    imdb_scraper = IMDBScraper()
    
    # Get current movies from iPlayer
    movies = iplayer_scraper.get_current_movies()
    logger.info(f"Found {len(movies)} movies on iPlayer")
    
    # Enrich movie data with IMDB information using parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Create a list of futures for parallel execution
        future_to_movie = {
            executor.submit(fetch_imdb_data, movie, imdb_scraper): movie
            for movie in movies
        }
        
        # Process completed futures as they come in
        enriched_movies = []
        for future in concurrent.futures.as_completed(future_to_movie):
            try:
                enriched_movie = future.result()
                enriched_movies.append(enriched_movie)
            except Exception as e:
                logger.error(f"Error processing movie: {str(e)}")
    
    logger.info(f"Successfully enriched {len(enriched_movies)} movies with IMDB data")
    
    # Generate HTML output
    output_path = generate_html(enriched_movies)
    logger.info(f"Process completed successfully. Output generated at: {output_path}")
    
    # TODO: Implement the following steps:
    # 3. Get ratings from Rotten Tomatoes
    # 4. Rank movies based on combined ratings
    # 5. Deploy webpage

if __name__ == "__main__":
    main() 
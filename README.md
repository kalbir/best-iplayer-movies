# Best iPlayer Movies

This project scrapes BBC iPlayer for available movies and ranks them based on ratings from Rotten Tomatoes and IMDB. The results are presented in a static webpage.

## Features

- Fetches current movies from BBC iPlayer
- Retrieves ratings from Rotten Tomatoes and IMDB
- Ranks movies based on combined ratings
- Generates a static webpage with the results
- Deploys the webpage to the internet

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys (if needed):
```bash
cp .env.example .env
```

4. Run the scraper:
```bash
python src/main.py
```

## Project Structure

```
best-iplayer-movies/
├── src/
│   ├── scrapers/
│   │   ├── iplayer.py
│   │   ├── rotten_tomatoes.py
│   │   └── imdb.py
│   ├── processors/
│   │   └── movie_ranker.py
│   ├── templates/
│   │   └── index.html
│   └── main.py
├── tests/
│   ├── test_scrapers/
│   └── test_processors/
├── static/
│   ├── css/
│   └── js/
├── output/
├── requirements.txt
└── README.md
```

## Development

- Use `black` for code formatting
- Use `flake8` for linting
- Run tests with `pytest`

## License

MIT 
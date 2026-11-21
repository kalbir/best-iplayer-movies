import os
import sys

# src/ modules import each other as top-level packages (e.g. `from scrapers.iplayer import ...`)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pathlib import Path

# Repo root. The price cache, debug dumps and bank_colors.json live here so
# they don't depend on the directory the app is started from.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

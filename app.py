"""Flask entrypoint. `flask run` auto-detects app.py:app."""
from zadok import create_app

app = create_app()

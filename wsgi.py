"""
WSGI config for Machining Calculator.

This module contains the WSGI application used by the application server.
"""

from app import create_app

# Create the Flask application at import time for WSGI servers.
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

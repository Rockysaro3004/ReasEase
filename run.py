"""
ReadEase Entry Point
Run this script to start the local development server:
    python run.py
"""
import os
from app import create_app

# Use FLASK_ENV or default to development
env_name = os.getenv('FLASK_ENV', 'development')
app = create_app(env_name)

if __name__ == '__main__':
    # Local development server with auto-reloader enabled
    print("=" * 60)
    print(" Starting ReadEase – Smart Reading Assistant for Students")
    print(" Local Server: http://127.0.0.1:5000")
    print(" Press Ctrl+C to stop the server.")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)

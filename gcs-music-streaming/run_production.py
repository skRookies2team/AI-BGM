"""
Production server using Waitress
"""
from waitress import serve
from music_service_gcs import app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8003))

if __name__ == '__main__':
    print("=" * 60)
    print("Music Recommendation Service (Production Mode)")
    print("=" * 60)
    print(f"Server running on http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    serve(app, host=HOST, port=PORT, threads=4)

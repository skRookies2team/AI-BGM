"""
FastAPI Server Runner with Uvicorn
Production-ready server for Music Streaming Service
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8003))

    print("=" * 60)
    print("FastAPI Music Streaming Service")
    print("=" * 60)
    print(f"Server running on http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Alternative Docs: http://{host}:{port}/redoc")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    # Run with Uvicorn
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,  # Set to True for development
        workers=1,     # Increase for production
        log_level="info"
    )

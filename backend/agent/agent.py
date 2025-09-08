"""
RAGBot Agent Entry Point
Main entry point for the RAGBot agent application.
This file imports the FastAPI app from main.py and serves as the application entry point.
"""
from main import app

# Export the app for use by ASGI servers like uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
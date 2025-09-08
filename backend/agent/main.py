"""
Main FastAPI application module for the RAGBot agent.
Sets up the FastAPI app and registers all route modules.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_SETTINGS
from routes import health, chat, tools, sessions, files, mcp_config

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="RAGBot Agent API",
        description="AI agent with RAG capabilities and MCP tool integration",
        version="2.0.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        **CORS_SETTINGS
    )

    # Register route modules
    app.include_router(health.router, tags=["Health"])
    app.include_router(chat.router, tags=["Chat"])
    app.include_router(tools.router, tags=["Tools"])
    app.include_router(sessions.router, tags=["Sessions"])
    app.include_router(files.router, tags=["Files"])
    app.include_router(mcp_config.router, tags=["MCP Config"])

    return app

# Create the app instance
app = create_app()

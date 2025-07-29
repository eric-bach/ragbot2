import os
import requests
import json
from typing import Dict, Any
from strands import tool
from linkup import LinkupClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('LINKUP_API_KEY')

@tool
def web_search(
    query: str 
) -> Dict[str, Any]:
    """
    Perform web search using Linkup's Web Search API.
    
    Args:
        query: The search query to perform
        
    Returns:
        Dictionary containing search results from Linkup API
    """
    
    try:
        client = LinkupClient(api_key=API_KEY)

        response = client.search(
            query=query,
            depth="standard",
            output_type="sourcedAnswer",
            include_images=False
        )
        
        return response
    
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "query": query
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse API response: {str(e)}",
            "query": query
        }

if __name__ == "__main__":
    response = web_search("What is the current price of bitcoin?")
    print(response)
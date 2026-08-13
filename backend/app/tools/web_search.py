import httpx
from app.tools.registry import Tool, tool_registry
from app.config import config

async def search_web(query: str) -> str:
    """
    Searches the web using Tavily Search API.
    """
    if not config.TAVILY_API_KEY:
        return "Web search is disabled because TAVILY_API_KEY is missing."
        
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": config.TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "include_answer": True,
        "max_results": 3
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=15.0)
            
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer')
            results = "\n".join([f"- {r['title']} ({r['url']}): {r['content']}" for r in data.get('results', [])])
            
            output = ""
            if answer:
                output += f"AI Summary: {answer}\n\n"
            if results:
                output += f"Search Results:\n{results}"
                
            return output if output else "No results found."
        else:
            return f"Failed to search web: {response.text}"
    except Exception as e:
        return f"Error searching web: {e}"

search_tool = Tool(
    name="search_web",
    description="Searches the internet for current information, news, or answers to questions.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query, e.g. 'latest AI news' or 'Bitcoin price'"
            }
        },
        "required": ["query"]
    },
    callable=search_web
)

tool_registry.register(search_tool)

import httpx
from app.tools.registry import Tool, tool_registry
from app.config import config

async def get_weather(location: str) -> str:
    """
    Fetches the current weather for a given location using OpenWeatherMap.
    """
    if not config.WEATHER_API_KEY:
        return "Weather tool is disabled because WEATHER_API_KEY is missing."
        
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={config.WEATHER_API_KEY}&units=metric"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            
        if response.status_code == 200:
            data = response.json()
            description = data['weather'][0]['description']
            temp = data['main']['temp']
            return f"The current weather in {location} is {description} with a temperature of {temp}°C."
        else:
            return f"Failed to get weather for {location}: {response.text}"
    except Exception as e:
        return f"Error fetching weather: {e}"

weather_tool = Tool(
    name="get_weather",
    description="Gets the current weather for a specified location.",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and country, e.g. 'Delhi, India'"
            }
        },
        "required": ["location"]
    },
    callable=get_weather
)

tool_registry.register(weather_tool)

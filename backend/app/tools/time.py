from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from app.tools.registry import Tool, tool_registry

def get_current_time(timezone_name: str) -> str:
    """
    Gets the current time for a specific timezone.
    """
    try:
        if not timezone_name or timezone_name.lower() == "utc":
            tz = ZoneInfo("UTC")
        else:
            tz = ZoneInfo(timezone_name)
            
        current_time = datetime.now(tz)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        return f"The current time in {timezone_name} is {formatted_time}."
    except ZoneInfoNotFoundError:
        return f"Error: Timezone '{timezone_name}' not found. Please use a valid IANA timezone name like 'Asia/Tokyo' or 'Europe/London'."
    except Exception as e:
        return f"Error getting time: {e}"

time_tool = Tool(
    name="get_time",
    description="Gets the current time for a specified timezone. You must provide a valid IANA timezone name (e.g., 'America/New_York', 'Asia/Tokyo', 'Europe/London', 'Asia/Kolkata').",
    parameters={
        "type": "object",
        "properties": {
            "timezone_name": {
                "type": "string",
                "description": "The IANA timezone name, e.g. 'Asia/Kolkata'"
            }
        },
        "required": ["timezone_name"]
    },
    callable=get_current_time
)

tool_registry.register(time_tool)

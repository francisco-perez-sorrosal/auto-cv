from crewai.tools import BaseTool
from datetime import datetime
from zoneinfo import ZoneInfo


class DateTimeTool(BaseTool):
    name: str = "Datetime Tool"
    description: str = "Get the current datetime."
        
    def _run(self) -> str:
        """
        Get tcurrent datetime as text
        """
        return datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d_%H-%M-%S")

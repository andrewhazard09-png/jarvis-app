import os
from dotenv import load_dotenv

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
WEATHER_KEY = os.getenv("WEATHER_API_KEY", "")
NEWS_KEY = os.getenv("NEWS_API_KEY", "")

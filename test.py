# Import relevant functionality
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
load_dotenv()

itinerary = open(f"examples/activities_city_Miami_4_bd881ed1-1792-4ffc-9c25-0e44539261c9.md", "r").read()

model = ChatOpenAI(model="gpt-5-mini")
response = model.invoke(f"Ere un experto en planficacion de viajes. Debes dar feedback sobre el siguiente itinerario de viaje: {itinerary}")
print(response.content)
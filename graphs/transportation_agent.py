from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from prompts.transportation_prompt import get_transportation_prompt
from models.itinerary import Itinerary

load_dotenv()

llm = init_chat_model("gpt-4o-mini", model_provider="openai")
# llm = init_chat_model("o4-mini-2025-04-16", model_provider="openai")

def generate_transportation_agent(itinerary: Itinerary):
    # prompt = get_transportation_prompt(itinerary)
    # result = llm.invoke(prompt)
    result = "Transportation details AGENT TEST"
    return result



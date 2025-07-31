from models.itinerary import Itinerary

def get_transportation_prompt(itinerary: Itinerary):

    return """
    You are a transportation expert.
    You are given a list of transportation options and a list of criteria.
    You need to select the best transportation option based on the criteria.
    """
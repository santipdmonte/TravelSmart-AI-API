from langchain_community.tools import TavilySearchResults

from dotenv import load_dotenv
load_dotenv()

def web_search(query: str):
    """
    Search the web for the query.
    """

    # Search
    tavily_search = TavilySearchResults(
        max_results=2,
        topic="general",
    )
    search_results = tavily_search.invoke(query)

    # Format
    formatted_results = "\n\n -- \n\n".join(
        [
            f"<Document href='{doc['url']}'/>\n{doc['content']}</Document>" 
            for doc in search_results
        ]
    )

    return {"messages": [formatted_results]}
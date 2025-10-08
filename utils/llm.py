from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.4,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# llm = ChatOpenAI(model="gpt-5")
# llm_cheap = ChatOpenAI(model="gpt-5-mini")

llm_cheap = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.4,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
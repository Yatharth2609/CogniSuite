from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
import os

# Local imports
from app.models import DataGenState

load_dotenv()

# Initialize the Azure OpenAI LLM
llm = AzureChatOpenAI(
    api_version="2024-10-21",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
)


def generate_data_node(state: DataGenState):
    """Generates JSON data based on the user's prompt."""
    print("---GENERATING SYNTHETIC DATA---")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at generating synthetic JSON data.
The user will provide a description of the data they want and a count of how many items to generate.
You must return a single, valid JSON array of objects. Do not include any markdown, backticks, or other text outside of the JSON array itself.
The generated data should be realistic and conform to the user's request."""),
        ("user",
         "Please generate {count} items based on this description: {prompt}")
    ]).format(prompt=state.prompt, count=state.count)

    try:
        response = llm.invoke(prompt)
        print("LLM response:", response)
    except Exception as e:
        print("LLM error:", e)
        state.generated_json = f"LLM error: {e}"
        return state

    # Extract the JSON string from the response
    state.generated_json = response.content

    return state


def create_data_gen_graph():
    """Creates the data generation agent graph."""
    workflow = StateGraph(DataGenState)
    workflow.add_node("generator", generate_data_node)
    workflow.set_entry_point("generator")
    workflow.add_edge("generator", END)
    graph = workflow.compile()
    return graph

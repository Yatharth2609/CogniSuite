from dotenv import load_dotenv
import os
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Local imports
from app.models import CodeAnalyzerState

load_dotenv()

# --- Initialize Azure Services ---
llm = AzureChatOpenAI(
    api_version="2024-10-21",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    temperature=0.0
)


def analyze_code(state: CodeAnalyzerState) -> CodeAnalyzerState:
    """Analyzes the given code and generates a high-level explanation."""
    print("---ANALYZING CODE---")

    prompt = ChatPromptTemplate.from_template("""You are an expert software engineer specializing in code review and documentation.
    Analyze the following code and provide a clear, high-level explanation. Structure your response in Markdown format.

    Your analysis should include:
    1.  **Purpose**: What is the primary goal of this code?
    2.  **Key Components**: Describe the main functions, classes, or variables.
    3.  **Logic Flow**: Explain how the code executes from start to finish.
    4.  **Potential Improvements**: Suggest one or two areas for refactoring or improvement.

    Here is the code:
        {code}
    """)

    # Invoke the LLM with the formatted prompt
    response=llm.invoke(prompt.format(code=state.code_content))

    # Save the generated analysis to the state
    state.analysis=response.content
    return state

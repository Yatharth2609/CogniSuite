from pydantic import BaseModel
from typing import List, Any
from langchain_core.documents import Document
from typing import List, Dict, Optional
from datetime import datetime
import base64

# Pydantic model for the SVG generation request
class SvgRequest(BaseModel):
    prompt: str

# Pydantic model for the state of our agent graph
# This is the corrected version
class AgentState(BaseModel):
    prompt: str
    svg_code: str = ""
    feedback: str = ""
    generation_attempts: int = 0

class DataGenRequest(BaseModel):
    prompt: str
    count: int

class DataGenState(BaseModel):
    prompt: str
    count: int
    generated_json: str = ""


class DocIntelState(BaseModel):
    """State for the document intelligence agent."""
    thread_id: str = ""
    document_content: List[Document] = []
    retriever: Any = None # We use Any because the retriever object is complex
    chat_history: List[str] = []
    question: str = ""
    answer: str = ""
    
class CodeAnalyzerState(BaseModel):
    """State for the code analyzer agent."""
    thread_id: str = ""
    code_content: str = ""
    analysis: str = ""
    
class VoiceAssistantState(BaseModel):
    """State for the voice assistant."""
    chat_history: List[Dict[str, str]] = []
    
class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatState(BaseModel):
    thread_id: str
    # A list of dictionaries, e.g., [{"role": "user", "content": "Hello"}]
    chat_history: List[Dict[str, str]] = []

class AgentState(BaseModel):
    # Input parameters
    prompt: str
    vector_format: str = "svg"  # svg, eps, pdf, ai
    style: str = "modern"  # modern, minimalist, detailed, artistic
    color_scheme: str = "default"  # default, monochrome, vibrant, pastel
    complexity: str = "medium"  # simple, medium, complex
    
    # Generation tracking
    generation_attempts: int = 0
    max_attempts: int = 3
    
    # Output results
    svg_code: Optional[str] = None
    vector_code: Optional[str] = None
    format_specific_code: Optional[Dict[str, str]] = {}
    
    # Validation and metadata
    is_valid: bool = False
    validation_errors: List[str] = []
    generation_metadata: Dict[str, Any] = {}
    
    # Multi-format support
    supported_formats: List[str] = ["svg", "eps", "pdf"]
    
    class Config:
        arbitrary_types_allowed = True



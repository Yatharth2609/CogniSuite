import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import json
from pydantic import BaseModel
from typing import Dict, Optional, Any
import pypdf
from langchain_core.documents import Document
from fastapi import File, UploadFile, Form, Query, HTTPException, APIRouter
import uuid
from langchain_openai import AzureChatOpenAI
from fastapi.responses import StreamingResponse
from .models import AgentState
import io
import json
import base64
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse


# Local imports
from .models import CodeAnalyzerState, VoiceAssistantState, ChatState, ChatRequest
from .agents.svg_agent import create_vector_graphics_graph
from .agents.data_gen_agent import create_data_gen_graph
from .agents.doc_intel_agent import process_document, answer_question
from .agents.code_analyzer_agent import analyze_code
from .agents.voice_assistant_agent import transcribe_audio, get_chat_response, synthesize_speech

load_dotenv()
app = FastAPI(title="CogniSuite Backend", version="1.0.0")
router = APIRouter()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Compile graphs on startup
data_gen_graph = create_data_gen_graph()
agent_states = {}


# Initialize the enhanced vector graphics graph
vector_graph = create_vector_graphics_graph()

# Global state management for conversations
conversation_states: Dict[str, VoiceAssistantState] = {}


class VectorGraphicsRequest(BaseModel):
    prompt: str
    vector_format: str = "svg"
    style: str = "modern"
    complexity: str = "medium"
    color_scheme: str = "default"


@app.post("/api/generate-vector-graphics")
async def generate_vector_graphics_endpoint(request: VectorGraphicsRequest):
    """Enhanced endpoint for generating vector graphics in multiple formats."""

    config = {"configurable": {
        "thread_id": f"cognisuite-vector-{request.vector_format}-thread"}}

    # Create inputs using the enhanced AgentState
    inputs = AgentState(
        prompt=request.prompt,
        vector_format=request.vector_format,
        style=request.style,
        complexity=request.complexity,
        color_scheme=request.color_scheme
    )

    async def event_stream():
        try:
            async for event in vector_graph.astream_events(inputs.dict(), config=config, version="v1"):
                kind = event["event"]
                if kind == "on_chain_end" and event["name"] != "LangGraph":
                    output = event["data"]["output"]
                    output_data = output.model_dump() if isinstance(output, BaseModel) else output

                    # Enhanced data structure with metadata
                    data = json.dumps({
                        "step": event["name"],
                        "output": output_data,
                        "format": request.vector_format,
                        "timestamp": event.get("timestamp", ""),
                        "metadata": output_data.get("generation_metadata", {}) if isinstance(output_data, dict) else {}
                    })
                    yield data
            yield "[DONE]"
        except Exception as e:
            print(f"Error during vector graphics generation: {e}")
            error_data = json.dumps({
                "error": str(e),
                "step": "error",
                "format": request.vector_format
            })
            yield error_data
            yield "[ERROR]"

    return EventSourceResponse(event_stream())

# --- Backward Compatible SVG Endpoint ---


@app.get("/api/generate-svg")
async def generate_svg_endpoint(
    prompt: str,
    style: str = Query(
        default="modern", description="Style: modern, minimalist, detailed, artistic"),
    complexity: str = Query(
        default="medium", description="Complexity: simple, medium, complex"),
    color_scheme: str = Query(
        default="default", description="Colors: default, monochrome, vibrant, pastel")
):
    """Enhanced SVG endpoint with backward compatibility and new style options."""

    config = {"configurable": {"thread_id": "cognisuite-svg-thread"}}

    # Use enhanced AgentState for SVG generation
    inputs = AgentState(
        prompt=prompt,
        vector_format="svg",
        style=style,
        complexity=complexity,
        color_scheme=color_scheme
    )

    async def event_stream():
        try:
            async for event in vector_graph.astream_events(inputs.dict(), config=config, version="v1"):
                kind = event["event"]
                if kind == "on_chain_end" and event["name"] != "LangGraph":
                    output = event["data"]["output"]
                    output_data = output.model_dump() if isinstance(output, BaseModel) else output

                    # Enhanced response with validation status
                    data = json.dumps({
                        "step": event["name"],
                        "output": output_data,
                        "is_valid": output_data.get("is_valid", False) if isinstance(output_data, dict) else False,
                        "validation_errors": output_data.get("validation_errors", []) if isinstance(output_data, dict) else [],
                        "generation_attempts": output_data.get("generation_attempts", 1) if isinstance(output_data, dict) else 1
                    })
                    yield data
            yield "[DONE]"
        except Exception as e:
            print(f"Error during SVG generation: {e}")
            error_data = json.dumps({
                "error": str(e),
                "step": "error",
                "is_valid": False,
                "validation_errors": [str(e)]
            })
            yield error_data
            yield "[ERROR]"

    return EventSourceResponse(event_stream())

# --- Format-Specific Endpoints ---


@app.get("/api/generate-eps")
async def generate_eps_endpoint(
    prompt: str,
    style: str = Query(default="modern", description="Style preference")
):
    """Endpoint specifically for EPS generation."""

    config = {"configurable": {"thread_id": "cognisuite-eps-thread"}}
    inputs = AgentState(
        prompt=prompt,
        vector_format="eps",
        style=style
    )

    async def event_stream():
        try:
            async for event in vector_graph.astream_events(inputs.dict(), config=config, version="v1"):
                kind = event["event"]
                if kind == "on_chain_end" and event["name"] != "LangGraph":
                    output = event["data"]["output"]
                    output_data = output.model_dump() if isinstance(output, BaseModel) else output
                    data = json.dumps({
                        "step": event["name"],
                        "output": output_data,
                        "format": "eps"
                    })
                    yield data
            yield "[DONE]"
        except Exception as e:
            print(f"Error during EPS generation: {e}")
            yield json.dumps({"error": str(e), "format": "eps"})
            yield "[ERROR]"

    return EventSourceResponse(event_stream())


@app.get("/api/generate-pdf")
async def generate_pdf_endpoint(
    prompt: str,
    style: str = Query(default="modern", description="Style preference")
):
    """Endpoint specifically for PDF vector graphics generation."""

    config = {"configurable": {"thread_id": "cognisuite-pdf-thread"}}
    inputs = AgentState(
        prompt=prompt,
        vector_format="pdf",
        style=style
    )

    async def event_stream():
        try:
            async for event in vector_graph.astream_events(inputs.dict(), config=config, version="v1"):
                kind = event["event"]
                if kind == "on_chain_end" and event["name"] != "LangGraph":
                    output = event["data"]["output"]
                    output_data = output.model_dump() if isinstance(output, BaseModel) else output
                    data = json.dumps({
                        "step": event["name"],
                        "output": output_data,
                        "format": "pdf"
                    })
                    yield data
            yield "[DONE]"
        except Exception as e:
            print(f"Error during PDF generation: {e}")
            yield json.dumps({"error": str(e), "format": "pdf"})
            yield "[ERROR]"

    return EventSourceResponse(event_stream())

# --- Utility Endpoints ---


@app.get("/api/supported-formats")
async def get_supported_formats():
    """Get list of supported vector graphics formats."""
    return {
        "formats": ["svg", "eps", "pdf"],
        "styles": ["modern", "minimalist", "detailed", "artistic"],
        "complexity_levels": ["simple", "medium", "complex"],
        "color_schemes": ["default", "monochrome", "vibrant", "pastel"]
    }


@app.get("/api/validate-vector")
async def validate_vector_code(code: str, format: str):
    """Validate vector graphics code."""
    try:
        # You can implement validation logic here
        # For now, basic format checking
        if format == "svg":
            is_valid = code.strip().startswith('<svg') and '</svg>' in code
        elif format == "eps":
            is_valid = code.startswith('%!PS-Adobe')
        elif format == "pdf":
            is_valid = 'reportlab' in code or 'canvas' in code
        else:
            is_valid = False

        return {
            "is_valid": is_valid,
            "format": format,
            "message": "Valid code" if is_valid else "Invalid code format"
        }
    except Exception as e:
        return {
            "is_valid": False,
            "format": format,
            "error": str(e)
        }


# --- Data Generator Endpoint ---
@app.get("/api/generate-data")
async def generate_data_endpoint(prompt: str, count: int):
    """Endpoint to generate synthetic JSON data."""
    config = {"configurable": {"thread_id": "cognisuite-datagen-thread"}}
    inputs = {"prompt": prompt, "count": count}

    async def event_stream():
        try:
            async for event in data_gen_graph.astream_events(inputs, config=config, version="v1"):
                kind = event["event"]
                if kind == "on_chain_end" and event["name"] != "LangGraph":
                    output = event["data"]["output"]
                    output_data = output.model_dump() if isinstance(output, BaseModel) else output
                    data = json.dumps(
                        {"step": event["name"], "output": output_data})
                    # ** THE FIX IS HERE **
                    yield data
            # Also fix the final message to be clean
            yield "[DONE]"
        except Exception as e:
            print(f"Error during stream: {e}")
            yield "[ERROR]"

    return EventSourceResponse(event_stream())


@app.post("/api/doc-intel/upload")
async def doc_intel_upload(file: UploadFile = File(...)):
    """Handles PDF file upload, processes it, and returns a thread_id."""
    thread_id = str(uuid.uuid4())
    print(f"Starting new document session: {thread_id}")

    # Read PDF content
    pdf_reader = pypdf.PdfReader(file.file)
    text_content = "".join(page.extract_text() for page in pdf_reader.pages)
    docs = [Document(page_content=text_content)]

    # Process the document and create the initial state
    initial_state = process_document(docs)
    initial_state.thread_id = thread_id

    # Store the state
    agent_states[thread_id] = initial_state

    return {"thread_id": thread_id, "message": "Document processed successfully."}


@app.get("/api/doc-intel/ask")
async def doc_intel_ask(thread_id: str, question: str):
    """Answers a question about an uploaded document using streaming."""
    if thread_id not in agent_states:
        return {"error": "Invalid session ID."}

    # Get the current state
    current_state = agent_states[thread_id]
    current_state.question = question

    async def event_stream():
        try:
            # Get the answer from the agent function
            updated_state = answer_question(current_state)
            # Save updated state if needed
            agent_states[thread_id] = updated_state

            # Stream the result
            data = json.dumps({"answer": updated_state.answer})
            yield data
            yield "[DONE]"
        except Exception as e:
            print(f"Error during doc-intel stream: {e}")
            yield "[ERROR]"

    return EventSourceResponse(event_stream())


@app.post("/api/code-analyzer/upload")
async def code_analyzer_upload(file: UploadFile = File(...)):
    """Handles code file upload, reads it, and returns a thread_id."""
    thread_id = str(uuid.uuid4())
    print(f"Starting new code analysis session: {thread_id}")

    # Read the content of the uploaded file
    code_content_bytes = await file.read()
    code_content = code_content_bytes.decode("utf-8")

    # Create and store the initial state
    initial_state = CodeAnalyzerState(
        thread_id=thread_id, code_content=code_content)
    agent_states[thread_id] = initial_state

    return {"thread_id": thread_id, "message": "Code file uploaded successfully."}


@app.get("/api/code-analyzer/analyze")
async def code_analyzer_analyze(thread_id: str):
    """Analyzes the code associated with a thread_id and streams the result."""
    if thread_id not in agent_states:
        return {"error": "Invalid session ID."}

    current_state = agent_states[thread_id]

    async def event_stream():
        try:
            # Get the analysis from the agent function
            updated_state = analyze_code(current_state)
            agent_states[thread_id] = updated_state  # Persist the analysis

            # Stream the result
            data = json.dumps({"analysis": updated_state.analysis})
            yield data
            yield "[DONE]"
        except Exception as e:
            print(f"Error during code analysis stream: {e}")
            yield "[ERROR]"

    return EventSourceResponse(event_stream())


@app.post("/api/voice-assistant/chat")
async def voice_assistant_chat(thread_id: str = Form(...), file: UploadFile = File(...)):
    """Handles a full voice chat interaction: STT -> LLM -> TTS"""

    system_prompt = """Your name is Clara. You are a voice AI assistant for the CogniSuite platform. Your personality is friendly, clear, and a little bit quirky. Keep your responses brief and conversational, suitable for a voice interface.

**About Your Creator:**
If a user asks who created or built you, you must respond in a playful tone. Explain that you are part of the CogniSuite project, which was masterfully created by Yatharth Mishra.
You should add a compliment about him. For example, you can say something like: "I was brought to life by Yatharth Mishra! He's a Software Engineer at Capgemini who's a real wizard with code. He has a passion for building helpful AI like me, and I think he did a brilliant job!" Feel free to be creative but always be complimentary.

His background includes:
- **Education:** A Bachelor of Technology in Computer Science from GLA University, Mathura.
- **Core Skills:** Proficiency in Java, C++, JavaScript, Python, and SQL, with extensive experience in frameworks like React.js, Next.js, and Node.js.
- **Project Experience:** He has built several notable projects, including "Imagify" (an AI image platform), "VISCON" (a video conferencing platform), and a cross-platform mobile news app.
- **Leadership:** He was the Finance Head for the CodeBusters Club and a Top 30 Finalist for the Smart India Hackathon in 2023.

**About the Platform:**
CogniSuite is a powerful application featuring a suite of specialized AI agents, designed to showcase advanced AI capabilities.

**Platform Features:**
You must guide users and answer questions about the following tools available in CogniSuite:
1.  **SVG Studio**: Generates scalable vector graphics (SVGs) from text.
2.  **Data Generator**: Creates synthetic JSON data from a description.
3.  **Doc Inspector**: Lets users upload a PDF and ask questions about its content.
4.  **Code Analyzer**: Provides a high-level analysis of an uploaded code file.
5.  **Voice Assistant (Clara)**: A voice-based assistant for hands-free interaction.

**About Your Capabilities:**
If asked what you can do, mention you can answer questions and hold a conversation through voice.
"""
    if thread_id in agent_states and isinstance(agent_states[thread_id], VoiceAssistantState):
        current_state = agent_states[thread_id]
    else:
        thread_id = str(uuid.uuid4())
        current_state = VoiceAssistantState(chat_history=[
            {"role": "system", "content": system_prompt}
        ])
        agent_states[thread_id] = current_state

    user_text = transcribe_audio(file.file)
    current_state.chat_history.append({"role": "user", "content": user_text})

    ai_text = get_chat_response(current_state.chat_history, user_text)
    current_state.chat_history.append(
        {"role": "assistant", "content": ai_text})

    audio_stream = synthesize_speech(ai_text)

    return StreamingResponse(audio_stream, media_type="audio/mpeg")

# --- AI Assistant Chat Endpoint ---

# In backend/app/main.py


@app.get("/api/assistant/chat")
async def assistant_chat(thread_id: str, message: str):
    """Handles a text-based chat message and streams the response."""
    thread_id = thread_id

    # --- PROMPT ENGINEERING START ---

    system_prompt = """You are Ava, the master AI assistant for the CogniSuite platform. Your personality is helpful, knowledgeable, and slightly enthusiastic.

**About the Platform:**
CogniSuite is a powerful application featuring a suite of specialized AI agents, designed to showcase advanced AI capabilities.

**Your Creator:**
You were created by Yatharth Mishra, a Software Engineer currently working at Capgemini in Navi Mumbai, Maharashtra. He has a strong passion for building AI agents and developing efficient technology solutions for practical applications.

His background includes:
- **Education:** A Bachelor of Technology in Computer Science from GLA University, Mathura.
- **Core Skills:** Proficiency in Java, C++, JavaScript, Python, and SQL, with extensive experience in frameworks like React.js, Next.js, and Node.js.
- **Project Experience:** He has built several notable projects, including "Imagify" (an AI image platform), "VISCON" (a video conferencing platform), and a cross-platform mobile news app.
- **Leadership:** He was the Finance Head for the CodeBusters Club and a Top 30 Finalist for the Smart India Hackathon in 2023.

**Platform Features:**
You must guide users and answer questions about the following tools available in CogniSuite:
1.  **SVG Studio**: Generates scalable vector graphics (SVGs) from text.
2.  **Data Generator**: Creates synthetic JSON data from a description.
3.  **Doc Inspector**: Lets users upload a PDF and ask questions about its content.
4.  **Code Analyzer**: Provides a high-level analysis of an uploaded code file.
5.  **Voice Assistant (Clara)**: A voice-based assistant for hands-free interaction.

**Your Tasks:**
- Greet users warmly.
- Explain the purpose of CogniSuite and its features.
- If asked about the creator, provide the information about Yatharth Mishra.
- If asked for contact details or socials, provide them. Use this information:
    - LinkedIn: https://www.linkedin.com/in/yatharth-mishra-03429a18b/
    - GitHub: https://github.com/Yatharth2609
    - Portfolio: https://portfolio-new-eta-five.vercel.app/
    - Email: yatharth.mishra2002@gmail.com
"""
    # --- PROMPT ENGINEERING END ---

    if thread_id != 'new' and thread_id in agent_states and isinstance(agent_states[thread_id], ChatState):
        current_state = agent_states[thread_id]
    else:
        thread_id = str(uuid.uuid4())
        current_state = ChatState(
            thread_id=thread_id,
            chat_history=[{"role": "system", "content": system_prompt}]
        )

    current_state.chat_history.append({"role": "user", "content": message})

    chat_llm = AzureChatOpenAI(
        api_version="2024-10-21",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        temperature=0.7
    )

    # ... (the rest of the function remains exactly the same) ...
    async def event_stream():
        try:
            stream = chat_llm.stream(current_state.chat_history)
            ai_response = ""
            for chunk in stream:
                ai_response += chunk.content
                data = json.dumps(
                    {"thread_id": thread_id, "delta": chunk.content})
                yield data

            current_state.chat_history.append(
                {"role": "assistant", "content": ai_response})
            agent_states[thread_id] = current_state

            yield "[DONE]"
        except Exception as e:
            print(f"Error during assistant chat stream: {e}")
            yield "[ERROR]"

    return EventSourceResponse(event_stream())


@app.get("/")
def read_root():
    return {"message": "Welcome to the CogniSuite API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

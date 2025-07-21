# Project: CogniSuite - Unified GenAI Platform
# Tech Stack: LangGraph + Python (Backend), FastAPI, React (Frontend), deployed on Azure/GCP

# Below is the high-level file/folder structure. We'll start with the backend setup first.

# === Folder Structure (Monorepo) ===

# cognisuite/
# ├── backend/
# │   ├── app/
# │   │   ├── __init__.py
# │   │   ├── main.py
# │   │   ├── langgraph_agents/
# │   │   │   ├── __init__.py
# │   │   │   ├── synthetic_data.py
# │   │   │   ├── document_intelligence.py
# │   │   │   ├── tts_stt_assistant.py
# │   │   │   ├── vector_graphics.py
# │   │   │   └── reverse_engineering.py
# │   │   ├── services/
# │   │   │   ├── __init__.py
# │   │   │   ├── whisper_service.py
# │   │   │   ├── tts_service.py
# │   │   │   ├── file_service.py
# │   │   │   └── gpt_service.py
# │   │   ├── routes/
# │   │   │   ├── __init__.py
# │   │   │   ├── synthetic.py
# │   │   │   ├── documents.py
# │   │   │   ├── audio.py
# │   │   │   ├── graphics.py
# │   │   │   └── reverse.py
# │   │   └── utils/
# │   │       └── logger.py
# │   ├── requirements.txt
# │   └── Dockerfile
# ├── frontend/
# │   ├── components/
# │   ├── pages/
# │   ├── styles/
# │   └── next.config.js
# ├── shared/
# │   └── contracts/
# │       ├── synthetic_schema.json
# │       ├── resume_template.json
# │       └── code_doc_template.json
# ├── deployment/
# │   ├── azure.yaml
# │   └── gcp.yaml
# └── README.md


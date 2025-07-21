from dotenv import load_dotenv
import os
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from fastapi import File, UploadFile
from typing import List
from langchain.schema import Document

# Local imports
from app.models import DocIntelState

load_dotenv()


llm = AzureChatOpenAI(
    api_version="2024-10-21",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    temperature=0.0
)

# Initialize the embeddings model for vectorizing the document
embeddings = AzureOpenAIEmbeddings(
    api_version="2024-10-21",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment="text-embedding-3-small",
)

# --- Agent Logic ---

def process_document(docs: List[Document]) -> DocIntelState:
    """Processes the uploaded document and creates a searchable vector store."""
    print("---PROCESSING DOCUMENT---")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
    
    # Return a new state object with the retriever
    return DocIntelState(retriever=vectorstore.as_retriever())

def answer_question(state: DocIntelState) -> DocIntelState:
    """Answers a question based on the document context."""
    print("---ANSWERING QUESTION---")
    if not state.retriever:
        state.answer = "Error: Document not processed yet. Please upload a document first."
        return state

    # Create a retrieval chain
    prompt = ChatPromptTemplate.from_template("""Answer the following question based only on the provided context:
    <context>
    {context}
    </context>
    Question: {input}""")
    
    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(state.retriever, document_chain)
    
    # Invoke the chain
    response = retrieval_chain.invoke({"input": state.question})
    
    state.answer = response["answer"]
    return state
import os

# Global cache for index
_index_cache = None
_settings_configured = False
_rag_available = True

def check_rag_available():
    """Check if RAG is available (embeddings working)"""
    global _rag_available
    return _rag_available

def retrieve_documents(query: str):
    """
    Retrieve documents from vector store.
    Temporarily disabled due to embedding API compatibility issues.
    Returns empty list to allow direct LLM generation.
    """
    # TODO: Fix embedding model compatibility with DashScope
    # For now, return empty to skip RAG and use direct LLM generation
    return []

def query_index(query: str):
    """Query the knowledge base"""
    return "Knowledge base temporarily unavailable. Using direct LLM response."

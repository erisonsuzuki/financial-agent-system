import logging

def setup_logging():
    logging.getLogger("langchain_groq").setLevel(logging.ERROR)
    logging.getLogger("langchain_nvidia_ai_endpoints").setLevel(logging.ERROR)

import logging

def setup_logging():
    logging.getLogger("langchain_groq").setLevel(logging.ERROR)

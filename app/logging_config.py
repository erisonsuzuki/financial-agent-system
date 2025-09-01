import logging

def setup_logging():
    logging.getLogger("langchain_google_genai._function_utils").setLevel(logging.ERROR)

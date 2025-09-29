import os
import uuid
import json
import pandas as pd
# from sqlalchemy import create_engine, inspect # Commented out
# import google.generativeai as genai # Commented out

from .utils import sanitize_name
from .schemas import QueryResponse, VisualizationSuggestion

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# --- Gemini API Configuration (Temporarily Disabled) ---
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# genai.configure(api_key=GEMINI_API_KEY)
# gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')
# --- ---

# --- Database Engine (Temporarily Disabled) ---
# DATABASE_URL = os.getenv("DATABASE_URL")
# engine = create_engine(DATABASE_URL)
# --- ---

def process_and_store_excel(file) -> (str, dict):
    """
    Reads an Excel file, cleans data, stores it in SQL tables, and returns a schema.
    """
    # This function will now do nothing and just return dummy data
    print("DEBUG: process_and_store_excel was called but is disabled.")
    upload_id = str(uuid.uuid4())
    dummy_schema = {"dummy_table": [{"name": "col1", "type": "TEXT"}]}
    return upload_id, dummy_schema

def query_data_with_llm(question: str, upload_id: str) -> QueryResponse:
    """
    Generates and executes a SQL query using Gemini, then generates a
    natural language response and visualization suggestion.
    """
    # This function will now do nothing and just return dummy data
    print("DEBUG: query_data_with_llm was called but is disabled.")
    return QueryResponse(
        natural_language_answer="The backend services are temporarily disabled for debugging.",
        query_result_data=[{"result": "dummy data"}],
        visualization_suggestion=VisualizationSuggestion(chart_type='table')
    )

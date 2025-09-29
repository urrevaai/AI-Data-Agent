import os
import uuid
import json
import logging
import pandas as pd
from sqlalchemy import inspect
import google.generativeai as genai

from .database import get_engine
from .utils import sanitize_name
from .schemas import QueryResponse, VisualizationSuggestion

from dotenv import load_dotenv
load_dotenv()

gemini_model = None

xdef list_compatible_gemini_models() -> list:
    """Return model names that support generateContent in current API version."""
    try:
        models = genai.list_models()
        compatible = []
        for m in models:
            supported = getattr(m, "supported_generation_methods", []) or []
            if "generateContent" in supported:
                compatible.append(getattr(m, "name", None))
        # Filter out any Nones and sort for stable output
        compatible = sorted([name for name in compatible if name])
        logging.debug(f"Compatible Gemini models: {compatible}")
        return compatible
    except Exception as exc:
        logging.warning(f"Could not list Gemini models: {exc}")
        return []

def get_gemini_model():
    """Lazily configures and returns the Gemini model on first use."""
    global gemini_model
    if gemini_model is None:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Discover compatible models and allow env override via GEMINI_MODEL
        compatible_models = list_compatible_gemini_models()
        env_model = os.getenv("GEMINI_MODEL")

        # Preference order if no env override or invalid value
        preferred_order = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro",
            "models/gemini-1.5-flash-8b",
            "models/gemini-1.0-pro",
        ]

        selected_model = None
        if env_model:
            if not compatible_models or env_model in compatible_models:
                selected_model = env_model
            else:
                logging.warning(
                    f"GEMINI_MODEL '{env_model}' not compatible. Falling back to a supported model."
                )

        if not selected_model:
            if compatible_models:
                # choose the first available from our preferred list; else first compatible
                for preferred in preferred_order:
                    if preferred in compatible_models:
                        selected_model = preferred
                        break
                if not selected_model:
                    selected_model = compatible_models[0]
            else:
                # Fallback to a commonly available model name when listing failed
                selected_model = "models/gemini-1.5-flash"

        print(f"DEBUG: Compatible Gemini models: {compatible_models}")
        print(f"DEBUG: Using Gemini model: {selected_model}")
        gemini_model = genai.GenerativeModel(selected_model)
        # --- END OF FIX ---

    return gemini_model

def process_and_store_excel(file) -> (str, dict):
    """Reads an Excel file, cleans it, and stores each sheet in the database."""
    engine = get_engine()
    upload_id = str(uuid.uuid4())
    xls = pd.ExcelFile(file)
    db_schema = {}

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name)
        df.columns = [sanitize_name(col) for col in df.columns]

        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col])
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=False, yearfirst=False).fillna(df[col])

        table_name = f"data_{upload_id}_{sanitize_name(sheet_name)}"
        df.to_sql(table_name, engine, index=False, if_exists='replace')

        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        db_schema[table_name] = [{"name": c['name'], "type": str(c['type'])} for c in columns]

    return upload_id, db_schema

def get_db_schema_string(upload_id: str) -> str:
    """Retrieves and formats the schema of tables for a given upload."""
    engine = get_engine()
    inspector = inspect(engine)
    schema_str = ""
    table_names = [name for name in inspector.get_table_names() if name.startswith(f"data_{upload_id}")]

    for table_name in table_names:
        schema_str += f"Table '{table_name}':\n"
        columns = inspector.get_columns(table_name)
        for column in columns:
            schema_str += f"  - {column['name']} ({str(column['type'])})\n"
    return schema_str

def query_data_with_llm(question: str, upload_id: str) -> QueryResponse:
    """Uses Gemini to convert a question to SQL, executes it, and formats the response."""
    engine = get_engine()
    model = get_gemini_model()
    schema_string = get_db_schema_string(upload_id)

    sql_prompt = f"""
    You are an expert SQLite data analyst. Based on the database schema below, write a single, valid SQL query that answers the user's question.
    Only output the SQL query and nothing else. Do not use markdown, code blocks, or any other formatting.
    ### Database Schema:
    {schema_string}
    ### User Question:
    {question}
    ### SQL Query:
    """

    sql_response = model.generate_content(sql_prompt)
    sql_query = sql_response.text.strip()

    if any(keyword in sql_query.upper() for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER']):
        raise ValueError("Generated query contains disallowed keywords.")

    with engine.connect() as connection:
        from sqlalchemy import text
        result = connection.execute(text(sql_query))
        column_names = list(result.keys())
        query_result_data = [dict(zip(column_names, row)) for row in result.fetchall()]

    summary_prompt = f"""
    You are a helpful data visualization assistant. Based on the user's original question and the data returned from the database, please do the following:
    1. Write a concise, natural language answer to the user's question.
    2. Suggest the best chart type for visualizing this data (e.g., 'bar', 'line', 'pie', 'table').
    3. Identify the column(s) for the x-axis and y-axis.
    4. Provide a descriptive title for the chart.
    Respond ONLY with a valid JSON object with the keys: "natural_language_answer", "chart_type", "x_axis", "y_axis", "title".
    The y_axis must be a list of strings. If the best visualization is a table, set chart_type to 'table' and other visualization keys to null.
    ### Original Question:
    {question}
    ### Data Returned from Query (first 5 rows):
    {pd.DataFrame(query_result_data).head().to_string()}
    ### JSON Response:
    """

    json_generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
    summary_response = model.generate_content(summary_prompt, generation_config=json_generation_config)
    
    cleaned_json_text = summary_response.text.strip().replace('```json', '').replace('```', '')
    summary_data = json.loads(cleaned_json_text)

    return QueryResponse(
        natural_language_answer=summary_data.get("natural_language_answer", "Could not generate a summary."),
        query_result_data=query_result_data,
        visualization_suggestion=VisualizationSuggestion(**summary_data)
    )
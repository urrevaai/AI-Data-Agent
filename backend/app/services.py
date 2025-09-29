import os
import io
import uuid
import json
import pandas as pd
from sqlalchemy import inspect, text
from dotenv import load_dotenv
import google.generativeai as genai

from .utils import sanitize_name
from .schemas import QueryResponse, VisualizationSuggestion
from .database import engine

# Load environment variables
load_dotenv()

# --- Gemini API Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
# Candidate models to try in order of preference (broad coverage across API versions)
_GEMINI_MODEL_CANDIDATES = [
    # Newer generations (will be skipped if not available in the project/region)
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-2.0-pro',
    # 1.5 series
    'gemini-1.5-flash-latest',
    'gemini-1.5-flash-002',
    'gemini-1.5-flash',
    'gemini-1.5-pro-latest',
    'gemini-1.5-pro-002',
    'gemini-1.5-pro',
    # 1.0 series and legacy
    'gemini-1.0-pro-001',
    'gemini-1.0-pro',
    'gemini-pro',
]
# Lazily instantiate models as needed
_MODEL_CACHE = {}

def _get_model(model_name: str):
    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = genai.GenerativeModel(model_name)
    return _MODEL_CACHE[model_name]

def _generate_with_fallback(prompt: str, require_json: bool = False):
    last_err = None
    # Allow override via env var
    env_model = os.getenv('GEMINI_MODEL')
    model_list = ([env_model] if env_model else []) + _GEMINI_MODEL_CANDIDATES
    for name in model_list:
        try:
            model = _get_model(name)
            if require_json:
                try:
                    cfg = genai.types.GenerationConfig(response_mime_type="application/json")
                    return model.generate_content(prompt, generation_config=cfg)
                except Exception as e_json:
                    # Retry without JSON config if not supported
                    return model.generate_content(prompt)
            else:
                return model.generate_content(prompt)
        except Exception as e:
            last_err = e
            continue
    # Convert to ValueError so the API can return a 400 instead of 500
    raise ValueError(f"Failed to generate content from Gemini models: {str(last_err)}")
# --- ---

# Use shared engine from database.py

def process_and_store_excel(file, filename: str | None = None) -> (str, dict):
    """
    Reads an Excel file, cleans data, stores it in SQL tables, and returns a schema.
    """
    upload_id = str(uuid.uuid4())
    safe_upload_id = upload_id.replace('-', '_')
    # Support both file-like objects and raw bytes
    if hasattr(file, 'read'):
        file_bytes = file.read()
    else:
        file_bytes = file
    db_schema = {}

    # Try to parse as Excel using extension hints
    xls = None
    if filename:
        lower_name = filename.lower()
        if lower_name.endswith('.xlsx'):
            try:
                xls = pd.ExcelFile(io.BytesIO(file_bytes), engine='openpyxl')
            except Exception:
                xls = None
        elif lower_name.endswith('.xls'):
            try:
                xls = pd.ExcelFile(io.BytesIO(file_bytes), engine='xlrd')
            except Exception:
                xls = None

    if xls is None:
        # Attempt Excel auto-detection: openpyxl then xlrd
        try:
            xls = pd.ExcelFile(io.BytesIO(file_bytes), engine='openpyxl')
        except Exception:
            try:
                xls = pd.ExcelFile(io.BytesIO(file_bytes), engine='xlrd')
            except Exception:
                xls = None

    if xls is not None:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name)
            df.columns = [sanitize_name(col) for col in df.columns]
            table_name = f"data_{safe_upload_id}_{sanitize_name(sheet_name)}"
            df.to_sql(table_name, engine, index=False, if_exists='replace')
            inspector = inspect(engine)
            columns = inspector.get_columns(table_name)
            db_schema[table_name] = [{"name": c['name'], "type": str(c['type'])} for c in columns]
        return upload_id, db_schema

    # Fallback: try CSV
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
        df.columns = [sanitize_name(col) for col in df.columns]
        base_name = os.path.splitext(filename or f'upload_{safe_upload_id}')[0]
        table_name = f"data_{safe_upload_id}_{sanitize_name(base_name)}"
        df.to_sql(table_name, engine, index=False, if_exists='replace')
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        db_schema[table_name] = [{"name": c['name'], "type": str(c['type'])} for c in columns]
        return upload_id, db_schema
    except Exception as e:
        raise ValueError("Unsupported or corrupt file. Please upload a valid .xlsx, .xls, or .csv file.") from e

def get_db_schema_string(upload_id: str) -> str:
    """
    Inspects the database and returns a string representation of the schema.
    """
    inspector = inspect(engine)
    safe_upload_id = upload_id.replace('-', '_')
    schema_str = ""
    table_names = [name for name in inspector.get_table_names() if name.startswith(f"data_{safe_upload_id}")]
    
    for table_name in table_names:
        schema_str += f"Table '{table_name}':\n"
        columns = inspector.get_columns(table_name)
        for column in columns:
            schema_str += f"  - {column['name']} ({str(column['type'])})\n"
    return schema_str

def query_data_with_llm(question: str, upload_id: str) -> QueryResponse:
    """
    Generates and executes a SQL query using Gemini, then generates a
    natural language response and visualization suggestion.
    """
    schema_string = get_db_schema_string(upload_id)

    # 1. First try: Gemini Natural Language to SQL
    sql_query = None
    if GEMINI_API_KEY and GEMINI_API_KEY.strip():
        sql_prompt = f"""
        You are an expert SQLite data analyst. Based on the database schema below, write a single, valid SQL query that answers the user's question.
        Requirements:
        - Query MUST read from one or more uploaded tables whose names start with 'data_{upload_id.replace('-', '_')}_'. Do NOT return a literal-only SELECT.
        - Provide meaningful column aliases for any expressions or literals (e.g., SELECT COUNT(*) AS total_count).
        - Prefer a LIMIT 100 unless the question specifies otherwise.
        - Only output the SQL query and nothing else. Do not use markdown, code blocks, or any other formatting.

        ### Database Schema:
        {schema_string}

        ### User Question:
        {question}

        ### SQL Query:
        """
        try:
            sql_response = _generate_with_fallback(sql_prompt, require_json=False)
            sql_query = sql_response.text.strip()
        except Exception:
            sql_query = None

    # Heuristic fallback: if no API key or generation failed, select top rows from first table
    if not sql_query:
        inspector = inspect(engine)
        safe_upload_id = upload_id.replace('-', '_')
        table_names = [name for name in inspector.get_table_names() if name.startswith(f"data_{safe_upload_id}")]
        if not table_names:
            raise ValueError("No tables found for this upload id.")
        first_table = table_names[0]
        sql_query = f"SELECT * FROM {first_table} LIMIT 50"

    # Normalize SQL: enforce single SELECT statement and remove trailing semicolon
    normalized_sql = sql_query.strip()
    if normalized_sql.endswith(';'):
        normalized_sql = normalized_sql[:-1].strip()
    if not normalized_sql.lower().startswith('select'):
        raise ValueError("Generated query is not a SELECT statement.")

    # SECURITY CHECK
    if any(keyword in sql_query.upper() for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER']):
        raise ValueError("Generated query contains disallowed keywords.")

    # 2. Execute the query
    try:
        with engine.connect() as connection:
            result = connection.execute(text(normalized_sql))
            column_names = list(result.keys())
            rows = result.fetchall()
            # Normalize generic/unnamed columns for better UI display
            normalized_columns = []
            for name in column_names:
                if not name or name.strip() in {"?column?", "", "column1"}:
                    normalized_columns.append("value")
                else:
                    normalized_columns.append(name)
            query_result_data = [dict(zip(normalized_columns, row)) for row in rows]
    except Exception as exec_err:
        raise ValueError(f"Failed to execute SQL: {str(exec_err)}") from exec_err

    # 3. Second Gemini call: Summarize results and suggest visualization in JSON
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

    # Configure the model to output JSON (or fallback to a minimal summary when no API key)
    if GEMINI_API_KEY and GEMINI_API_KEY.strip():
        try:
            summary_response = _generate_with_fallback(summary_prompt, require_json=True)
        except Exception:
            summary_response = _generate_with_fallback(summary_prompt, require_json=False)

        # Try to parse JSON; if it fails, fall back to minimal defaults
        try:
            summary_data = json.loads(summary_response.text)
        except Exception:
            summary_data = {
                "natural_language_answer": summary_response.text.strip()[:500],
                "chart_type": "table",
                "x_axis": None,
                "y_axis": None,
                "title": "Query Result",
            }
    else:
        # No API key: build a simple summary locally
        summary_data = {
            "natural_language_answer": "Here are the first rows from your uploaded data.",
            "chart_type": "table",
            "x_axis": None,
            "y_axis": None,
            "title": "Query Result",
        }
    
    return QueryResponse(
        natural_language_answer=summary_data.get("natural_language_answer", "Could not generate a summary."),
        query_result_data=query_result_data,
        visualization_suggestion=VisualizationSuggestion(**summary_data)
    )
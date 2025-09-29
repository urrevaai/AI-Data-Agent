import os
import uuid
import json
import logging
import pandas as pd
from sqlalchemy import inspect, text
import google.generativeai as genai

from .database import get_engine
from .utils import sanitize_name
from .schemas import QueryResponse, VisualizationSuggestion

from dotenv import load_dotenv
load_dotenv()

gemini_model = None

def get_gemini_model():
    """Lazily configures and returns the Gemini model on first use."""
    global gemini_model
    if gemini_model is None:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        
        genai.configure(api_key=GEMINI_API_KEY)
        model_name = "models/gemini-2.5-flash-preview-05-20"
        print(f"DEBUG: Using confirmed available Gemini model: {model_name}")
        gemini_model = genai.GenerativeModel(model_name)
    return gemini_model

def process_and_store_excel(file) -> (str, dict):
    """Reads an Excel file, cleans it, and stores each sheet in the database."""
    engine = get_engine()
    upload_id = str(uuid.uuid4()).replace('-', '_')
    xls = pd.ExcelFile(file)
    db_schema = {}

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name)
        df.columns = [sanitize_name(col) for col in df.columns]

        for col in df.columns:
            # Attempt to convert to numeric, coercing errors to NaN
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            
            # Check if the column is primarily numeric
            non_null_count = df[col].notna().sum()
            if non_null_count > 0 and (numeric_col.notna().sum() / non_null_count) > 0.8:
                 df[col] = numeric_col
            else:
                # If not primarily numeric, try to convert to datetime
                if pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                    datetime_col = pd.to_datetime(df[col], errors='coerce')
                    if datetime_col.notna().sum() > 0:
                        df[col] = datetime_col

        table_name = f"data_{upload_id}_{sanitize_name(sheet_name)}"
        
        # Replace all Pandas null types (NaN, NaT) with None for SQL NULL
        df_for_sql = df.astype(object).where(pd.notnull(df), None)
        df_for_sql.to_sql(table_name, engine, index=False, if_exists='replace')

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
        schema_str += f'Table "{table_name}":\n'
        columns = inspector.get_columns(table_name)
        for column in columns:
            schema_str += f'  - "{column["name"]}" ({str(column["type"])})\n'
    return schema_str

def query_data_with_llm(question: str, upload_id: str) -> QueryResponse:
    """Uses Gemini to convert a question to SQL, executes it, and formats the response."""
    engine = get_engine()
    model = get_gemini_model()
    schema_string = get_db_schema_string(upload_id)

    # --- THIS IS THE FINAL, DEFINITIVE PROMPT FIX ---
    sql_prompt = f"""
    You are an expert PostgreSQL data analyst. Your database is PostgreSQL.
    Based on the database schema below, write a single, valid PostgreSQL query that answers the user's question.
    You MUST enclose all table and column names in double quotes (e.g., "my_table").
    To perform calculations on numeric columns, you MUST cast them to a decimal type, like this: CAST("my_column" AS DECIMAL). Do NOT cast to INTEGER.
    To format dates, use TO_CHAR("date_column_name"::timestamp, 'YYYY-MM').
    Only output the SQL query and nothing else. Do not use markdown.

    ### Database Schema:
    {schema_string}

    ### User Question:
    {question}

    ### SQL Query:
    """
    # --- END OF FIX ---

    sql_response = model.generate_content(sql_prompt)
    sql_query = sql_response.text.strip()

    if any(keyword in sql_query.upper() for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER']):
        raise ValueError("Generated query contains disallowed keywords.")

    with engine.connect() as connection:
        result = connection.execute(text(sql_query))
        column_names = list(result.keys())
        query_result_data = [dict(zip(column_names, row)) for row in result.fetchall()]

    summary_prompt = f"""
    You are a helpful data visualization assistant. Based on the user's original question and the data returned from the database, please do the following:
    1. A concise, natural language answer.
    2. The best chart type.
    3. Columns for x-axis and y-axis.
    4. A descriptive title.
    Respond ONLY with a valid JSON object with the keys: "natural_language_answer", "chart_type", "x_axis", "y_axis", "title".
    The y_axis must be a list of strings. For a table, set chart_type to 'table' and other keys to null.

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
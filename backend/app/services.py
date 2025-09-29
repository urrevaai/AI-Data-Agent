import os
import uuid
import json
import logging
import re
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
            # --- THIS IS THE ULTIMATE DATA CLEANING FIX ---
            # Step 1: Attempt to convert the column to numeric. 'coerce' will turn non-numeric values into NaN.
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            
            # Step 2: Check if the column is primarily numeric to avoid misinterpreting IDs as dates.
            # We check if more than 80% of the non-null values are numbers.
            non_null_count = df[col].notna().sum()
            if non_null_count > 0 and (numeric_col.notna().sum() / non_null_count) > 0.8:
                 df[col] = numeric_col
            else:
                # Step 3: If not primarily numeric, THEN attempt to convert to datetime.
                # This is a safer check for columns with mixed types or date-like strings.
                if pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                    datetime_col = pd.to_datetime(
                        df[col], errors='coerce', infer_datetime_format=True
                    )
                    # Only apply the conversion if it results in at least one valid date.
                    if datetime_col.notna().sum() > 0:
                        df[col] = datetime_col
            # --- END OF FIX ---

        table_name = f"data_{upload_id}_{sanitize_name(sheet_name)}"
        
        # Step 4: Final conversion to handle database types.
        # Replace all Pandas null types (NaN, NaT) with None, which becomes SQL NULL.
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

def _detect_dialect() -> str:
    """Return 'sqlite' or 'postgresql' based on the SQLAlchemy engine URL."""
    engine = get_engine()
    url = str(engine.url).lower()
    if "sqlite" in url:
        return "sqlite"
    if "postgresql" in url or "postgres" in url:
        return "postgresql"
    # Default to sqlite behavior if unknown
    return "sqlite"

def _normalize_sql_for_sqlite(sql: str) -> str:
    """Convert common PostgreSQL syntax to SQLite-compatible where possible."""
    normalized = sql
    # Remove explicit casts ::type
    normalized = normalized.replace("::timestamp", "")
    normalized = normalized.replace("::date", "")
    # Replace date formatting to SQLite strftime
    # e.g., TO_CHAR(date_col::timestamp, 'YYYY-MM') -> strftime('%Y-%m', date_col)
    normalized = normalized.replace("TO_CHAR(", "strftime('%Y-%m', ")
    normalized = normalized.replace("'YYYY-MM')", ")")
    # ILIKE to LIKE (case-insensitive requires lower()) — best-effort only
    normalized = normalized.replace(" ILIKE ", " LIKE ")
    return normalized

def _quote_table_identifiers(sql: str, table_names: list) -> str:
    """Ensure table names with dashes or mixed case are quoted in FROM/JOIN/UPDATE clauses."""
    normalized = sql
    for table in table_names:
        unquoted_pattern = rf'(?<!["])\b{re.escape(table)}\b'
        normalized = re.sub(unquoted_pattern, f'"{table}"', normalized)
    return normalized

def _normalize_sql_for_postgres(sql: str, table_names: list) -> str:
    """Convert common SQLite syntax to PostgreSQL-compatible and harden numeric/date handling."""
    normalized = sql
    # Backticks -> double quotes
    normalized = normalized.replace('`', '"')
    # Quote known table identifiers
    normalized = _quote_table_identifiers(normalized, table_names)
    # STRFTIME patterns -> to_char
    normalized = re.sub(r"STRFTIME\(\s*'%Y-%m'\s*,\s*([^)]+)\)", r"to_char(\1::timestamp, 'YYYY-MM')", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"STRFTIME\(\s*'%Y'\s*,\s*([^)]+)\)", r"to_char(\1::timestamp, 'YYYY')", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"STRFTIME\(\s*'%m'\s*,\s*([^)]+)\)", r"to_char(\1::timestamp, 'MM')", normalized, flags=re.IGNORECASE)
    # Lowercase variants
    normalized = re.sub(r"strftime\(\s*'%Y-%m'\s*,\s*([^)]+)\)", r"to_char(\1::timestamp, 'YYYY-MM')", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"strftime\(\s*'%Y'\s*,\s*([^)]+)\)", r"to_char(\1::timestamp, 'YYYY')", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"strftime\(\s*'%m'\s*,\s*([^)]+)\)", r"to_char(\1::timestamp, 'MM')", normalized, flags=re.IGNORECASE)
    # TO_TIMESTAMP(col) -> col::timestamp to avoid epoch overflow from scientific notation
    normalized = re.sub(r"TO_TIMESTAMP\(\s*([\"A-Za-z0-9_\.]+)\s*\)", r"\1::timestamp", normalized, flags=re.IGNORECASE)
    # CAST(x AS DECIMAL) -> robust numeric coercion to avoid errors on mixed text
    def _robust_numeric_cast(match: re.Match) -> str:
        inner = match.group(1)
        # Strip any surrounding quotes if already present
        inner_expr = inner.strip()
        return f"NULLIF(regexp_replace({inner_expr}::text, '[^0-9\\.\\-]', '', 'g'), '')::numeric"
    normalized = re.sub(r"CAST\(\s*(.*?)\s+AS\s+DECIMAL\s*\)", _robust_numeric_cast, normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"CAST\(\s*(.*?)\s+AS\s+DOUBLE\s+PRECISION\s*\)", _robust_numeric_cast, normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"CAST\(\s*(.*?)\s+AS\s+FLOAT\s*\)", _robust_numeric_cast, normalized, flags=re.IGNORECASE)
    # INTEGER casts should also be robust; convert CAST(x AS INTEGER) if present
    normalized = re.sub(r"CAST\(\s*(.*?)\s+AS\s+INT(EGER)?\s*\)", _robust_numeric_cast, normalized, flags=re.IGNORECASE)
    # SUM(CAST(x AS INTEGER)) variants
    normalized = re.sub(r"SUM\(\s*CAST\(\s*(.*?)\s+AS\s+INT(EGER)?\s*\)\s*\)", r"SUM( (NULLIF(regexp_replace(\1::text, '[^0-9\\.\\-]', '', 'g'), ''))::numeric )", normalized, flags=re.IGNORECASE)
    return normalized

def query_data_with_llm(question: str, upload_id: str) -> QueryResponse:
    """Uses Gemini to convert a question to SQL, executes it, and formats the response."""
    engine = get_engine()
    model = get_gemini_model()
    schema_string = get_db_schema_string(upload_id)

    dialect = _detect_dialect()
    if dialect == "sqlite":
        sql_prompt = f"""
        You are an expert SQLite data analyst. Your database is SQLite.
        Based on the database schema below, write a single, valid SQLite query that answers the user's question.
        Enclose table and column names in double quotes (e.g., "my_table").
        To format dates to year-month, use strftime('%Y-%m', "date_column_name").
        Only output the SQL query and nothing else. Do not use markdown.

        ### Database Schema:
        {schema_string}

        ### User Question:
        {question}

        ### SQL Query:
        """
    else:
        sql_prompt = f"""
        You are an expert PostgreSQL data analyst. Your database is PostgreSQL.
        Based on the database schema below, write a single, valid PostgreSQL query that answers the user's question.
        You MUST enclose all table and column names in double quotes (e.g., "my_table").
        To format dates, use to_char("date_column_name"::timestamp, 'YYYY-MM').
        Only output the SQL query and nothing else. Do not use markdown.

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

    def _try_execute(sql_to_run: str):
        with engine.connect() as connection:
            result = connection.execute(text(sql_to_run))
            cols = list(result.keys())
            rows = [dict(zip(cols, row)) for row in result.fetchall()]
            return rows, cols

    try:
        query_result_data, column_names = _try_execute(sql_query)
    except Exception as first_exc:
        # Attempt normalization and one retry
        if dialect == "sqlite":
            normalized_query = _normalize_sql_for_sqlite(sql_query)
        else:
            # Gather table names from our schema to ensure they are quoted
            inspector = inspect(engine)
            table_names = [name for name in inspector.get_table_names() if name.startswith(f"data_{upload_id}")]
            normalized_query = _normalize_sql_for_postgres(sql_query, table_names)
        logging.warning(f"Initial SQL failed, retrying with normalized SQL. Error: {first_exc}")
        query_result_data, column_names = _try_execute(normalized_query)

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
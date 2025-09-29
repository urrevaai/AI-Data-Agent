import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import services, schemas

app = FastAPI(
    title="AI Data Agent API (Gemini Edition)",
    description="API for chatting with your Excel data using Google Gemini.",
    version="1.0.0"
)

# --- Flexible CORS Configuration ---
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Root endpoint to confirm the server is running."""
    return {"message": "Welcome to the AI Data Agent API (Gemini Edition)!"}


@app.post("/upload", response_model=schemas.UploadResponse)
async def upload_excel_file(file: UploadFile = File(...)):
    """Handles Excel file uploads, processing, and storage."""
    try:
        if not file.filename.endswith(('.xls', '.xlsx')):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")
        
        # Use the real services file to process the data
        upload_id, schema = services.process_and_store_excel(file.file)
        
        return schemas.UploadResponse(
            upload_id=upload_id,
            message="File processed successfully.",
            file_name=file.filename,
            schema=schema
        )
    except Exception as e:
        # Log any crash and return a 500 error
        logging.exception("An error occurred in upload_excel_file:")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during file upload.")


@app.post("/query", response_model=schemas.QueryResponse)
async def query_data(request: schemas.QueryRequest):
    """Handles natural language queries against the uploaded data."""
    try:
        response = services.query_data_with_llm(
            question=request.question,
            upload_id=request.upload_id
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logging.exception("An error occurred in query_data:")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during query processing.")


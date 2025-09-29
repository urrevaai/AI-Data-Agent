import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import services, schemas

app = FastAPI(
    title="AI Data Agent API (Gemini Edition)",
    description="API for chatting with your Excel data using Google Gemini.",
    version="1.0.0"
)

# --- This is the new, flexible way to handle CORS ---
# It reads the allowed URLs from an environment variable.
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- The app.mount line has been REMOVED ---
# This is no longer needed because Vercel is serving your frontend.

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Data Agent API (Gemini Edition)!"}


@app.post("/upload", response_model=schemas.UploadResponse)
async def upload_excel_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")
    
    try:
        # Note: I've updated this to match the latest schema version
        upload_id, schema = services.process_and_store_excel(file.file)
        return schemas.UploadResponse(
            upload_id=upload_id,
            message="File processed successfully.",
            file_name=file.filename,
            schema=schema
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.post("/query", response_model=schemas.QueryResponse)
async def query_data(request: schemas.QueryRequest):
    try:
        response = services.query_data_with_llm(
            question=request.question,
            upload_id=request.upload_id
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during query processing: {str(e)}")

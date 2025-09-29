import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DEBUGGING SERVER")

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
    return {"message": "Bare-bones server is running!"}

# This is a FAKE upload endpoint. It does NOT process the file.
# It only proves that the server can receive a request without crashing.
@app.post("/upload")
async def fake_upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file received.")
    
    print(f"DEBUG: Received file named '{file.filename}'. Not processing it.")
    
    # Return a fake, hardcoded response
    return {
        "upload_id": "fake-id-12345",
        "message": "File received but not processed (DEBUG MODE).",
        "file_name": file.filename,
        "schema": {"debug_sheet": [{"name": "col1", "type": "TEXT"}]}
    }

@app.post("/query")
async def fake_query(request: dict):
     # Return a fake, hardcoded response
    return {
        "natural_language_answer": "This is a fake response from the debug server.",
        "query_result_data": [{"result": "ok"}],
        "visualization_suggestion": {"chart_type": "table"}
    }


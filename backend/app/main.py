import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DEBUGGING SERVER")

# We get the Vercel URL from an environment variable
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
    return {"message": "The bare-bones debug server is running!"}

# This is a FAKE upload endpoint. It only proves the connection works.
@app.post("/upload")
async def fake_upload(file: UploadFile = File(...)):
    print(f"DEBUG: Received file '{file.filename}'. Sending fake success response.")
    return {
        "upload_id": "fake-id-12345",
        "message": "File received by debug server!",
        "file_name": file.filename,
        "schema": {"debug_sheet": [{"name": "col1", "type": "TEXT"}]}
    }
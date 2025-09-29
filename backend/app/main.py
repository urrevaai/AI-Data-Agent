import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# --- THIS IS THE CRUCIAL DEBUGGING CODE ---
# We will print the variable the moment the server starts.
raw_origins = os.getenv("ALLOWED_ORIGINS", "NOT_SET")
print("--- DEBUGGING CORS ---")
print(f"RAW 'ALLOWED_ORIGINS' variable from Render: '{raw_origins}'")
parsed_origins = raw_origins.split(",")
print(f"PARSED list of origins: {parsed_origins}")
print("--- END DEBUGGING ---")
# --- ---

app = FastAPI(title="ULTIMATE DEBUGGING SERVER")

app.add_middleware(
    CORSMiddleware,
    allow_origins=parsed_origins, # Use the parsed list
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "The ultimate debug server is running!"}

@app.post("/upload")
async def fake_upload(file: UploadFile = File(...)):
    print(f"DEBUG: Received file '{file.filename}'.")
    return {"message": "Fake success from the ultimate debug server!"}


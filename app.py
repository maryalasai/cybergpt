import socket
from fastapi import FastAPI, File, UploadFile, HTTPException,Form
from fastapi.middleware.cors import CORSMiddleware


import pandas as pd
import io
from pydantic import BaseModel
import requests # type: ignore

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

class MessageRequest(BaseModel):
    message: str
SERVER_URL = "http://localhost:11434/api/generate" 

@app.post("/analyze/")
async def analyze_file_and_chat(
    message: str = Form(...),  # Accept `message` as a form field
    file: UploadFile = File(...)  # Accept `file` as a file upload
):
    if file.content_type not in ["text/plain", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        raise HTTPException(status_code=400, detail="Only text or Excel files are supported.")

    # Extract file content
    try:
        if file.content_type == "text/plain":
            file_content = (await file.read()).decode("utf-8")
            data = file_content
        elif file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            file_content = await file.read()
            df = pd.read_excel(io.BytesIO(file_content))
            data = df.to_string(index=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    # Construct the prompt for the model
    prompt = f"Data:\n{data}\n\nUser: {message}\nResponse:"

    # Send the data to the model server
    PAYLOAD = {
        "model": "llama2",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(SERVER_URL, json=PAYLOAD, headers={"Content-Type": "application/json"})
        response.raise_for_status()  # Raise an error for HTTP status codes 4xx/5xx

        llama_response = response.json()  # Parse the JSON response

        return {"response": llama_response}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with the model server: {str(e)}")


@app.get("/status/")
def status():
    SERVER_URL = "http://localhost:11434/api/generate"  # Replace with your server's URL
    PAYLOAD = {
        "model": "llama2",
        "prompt": "capital of india?",
        "stream": False
    }

    try:
        # Make a POST request to the model server
        response = requests.post(SERVER_URL, json=PAYLOAD, headers={"Content-Type": "application/json"})
        response.raise_for_status()  # Raise an error for HTTP status codes 4xx/5xx

        llama_response = response.json()  # Parse the JSON response

        return {
            "status": "Server is running.",
            "llama_connection": "Successful",
            "llama_response": llama_response  # Include the server's response
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "Server is running.",
            "llama_connection": f"Failed: {str(e)}",
            "llama_response": None
        }




import socket
from fastapi import FastAPI, File, UploadFile, HTTPException
import pandas as pd
import io
from pydantic import BaseModel
import requests # type: ignore

app = FastAPI()

SERVER_IP = "35.154.221.179"  # Replace with the IP address of the server
SERVER_PORT = 11434  # Replace with the port where the model is running

class MessageRequest(BaseModel):
    message: str

@app.post("/analyze/")
async def analyze_file_and_chat(message: MessageRequest, file: UploadFile = File(...)):
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

    # Construct input for the model
    user_message = message.message
    model_input = f"Data:\n{data}\n\nUser: {user_message}\nResponse:"

    # Send the data to the server
    try:
        with socket.create_connection((SERVER_IP, SERVER_PORT), timeout=300) as sock:
            sock.sendall(model_input.encode('utf-8'))  # Send the input to the model
            response = sock.recv(4096)  # Receive the response (adjust buffer size if needed)

        return {"response": response.decode('utf-8')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with the model server: {str(e)}")

@app.get("/status/")
def status():
    SERVER_URL = "http://35.154.221.179:11434/api/generate"  # Replace with your server's URL
    
    MESSAGE = {"message": "hi"}

    try:
        response = requests.post(SERVER_URL, json=MESSAGE, headers={"Content-Type": "application/json"})
        return {
            "status": "Server is running.",
            "llama_connection": "Successful",
            "llama_response": response
        }
    except Exception as e:
        return {
            "status": "Server is running.",
            "llama_connection": f"Failed: {str(e)}",
            "llama_response": None
        }



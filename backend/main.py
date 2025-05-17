from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pyngrok import ngrok
import uvicorn
import asyncio
from typing import Dict
from pydantic import BaseModel
import uuid

app = FastAPI()

# In-memory storage
users: Dict[str, str] = {}  # Maps name -> id
connections: Dict[str, WebSocket] = {}  # Maps user_id -> WebSocket

# Pydantic models for request/response validation
class CreateUserRequest(BaseModel):
    name: str

class SendMessageRequest(BaseModel):
    recipient_id: str
    message: str

@app.post("/api/users/create")
async def create_user(request: CreateUserRequest):
    if request.name in users:
        raise HTTPException(status_code=409, detail="Username already exists")
    user_id = str(uuid.uuid4())
    users[request.name] = user_id
    return {"id": user_id}

@app.get("/api/users/list")
async def list_users():
    return {"users": {name: id for name, id in users.items()}}

@app.post("/api/messages/send")
async def send_message(request: SendMessageRequest):
    if request.recipient_id not in connections:
        raise HTTPException(status_code=404, detail="Recipient not found or not connected")
    
    # Find sender's name
    sender_name = None
    for name, id in users.items():
        if id == request.recipient_id:
            sender_name = name
            break

    # Send message through WebSocket
    await connections[request.recipient_id].send_json({
        "from": sender_name,
        "message": request.message
    })
    
    return {
        "status": "success",
        "details": f"Message sent to recipient_id: {request.recipient_id}"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Get authentication data
        auth_data = await websocket.receive_json()
        user_id = auth_data.get("id")
        
        # Validate user_id
        if not any(id == user_id for id in users.values()):
            await websocket.close(code=4001, reason="Invalid user ID")
            return
        
        # Store connection
        connections[user_id] = websocket
        print(f"[Server] User with ID '{user_id}' connected")
        
        # Keep connection alive and handle incoming messages
        while True:
            await websocket.receive_text()  # Just keep connection alive
            
    except WebSocketDisconnect:
        if user_id in connections:
            del connections[user_id]
            print(f"[Server] User with ID '{user_id}' disconnected")

if __name__ == "__main__":
    public_url = ngrok.connect(8000, "http")
    print(f"[Server] Public URL: {public_url}")
    print(f"[Server] WebSocket URL: {public_url}/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status, Header
from pyngrok import ngrok
import uvicorn
import asyncio
from typing import Dict, Optional, Union
from pydantic import BaseModel
import uuid
from enum import IntEnum

app = FastAPI()

# In-memory storage
users: Dict[str, str] = {}  # Maps name -> id
connections: Dict[str, WebSocket] = {}  # Maps user_id -> WebSocket

# WebSocket Close Codes (RFC 6455)
class WSCloseCode(IntEnum):
    NORMAL_CLOSURE = 1000
    GOING_AWAY = 1001
    PROTOCOL_ERROR = 1002
    UNSUPPORTED_DATA = 1003
    INVALID_DATA = 1007
    POLICY_VIOLATION = 1008
    MESSAGE_TOO_BIG = 1009
    MANDATORY_EXTENSION = 1010
    INTERNAL_ERROR = 1011
    SERVICE_RESTART = 1012
    TRY_AGAIN_LATER = 1013
    BAD_GATEWAY = 1014
    TLS_HANDSHAKE = 1015
    
    # Custom close codes (4000-4999 range is reserved for private use)
    AUTHENTICATION_FAILED = 4001
    INVALID_USER = 4002
    SESSION_EXPIRED = 4003

# Message Status Codes
class MessageStatus(IntEnum):
    DELIVERED = 200
    QUEUED = 202
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

# Pydantic models for request/response validation
class CreateUserRequest(BaseModel):
    name: str

class CreateUserResponse(BaseModel):
    id: str
    status: int = status.HTTP_201_CREATED

class SendMessageRequest(BaseModel):
    recipient_name: str
    message: str

class SendMessageResponse(BaseModel):
    message_id: str
    status: MessageStatus
    details: str

class MessageDelivery(BaseModel):
    from_user: str
    message: str
    timestamp: float
    message_id: str

@app.post("/api/users/create", 
         response_model=CreateUserResponse,
         status_code=status.HTTP_201_CREATED)
async def create_user(request: CreateUserRequest):
    if request.name in users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    user_id = str(uuid.uuid4())
    users[request.name] = user_id
    return CreateUserResponse(id=user_id)

@app.get("/api/users/list",
         status_code=status.HTTP_200_OK)
async def list_users():
    return {
        "status": status.HTTP_200_OK,
        "users": {name: id for name, id in users.items()}
    }

@app.post("/api/messages/send",
          response_model=SendMessageResponse,
          status_code=status.HTTP_200_OK)
async def send_message(
    request: SendMessageRequest,
    x_user_id: Union[str, None] = Header(default=None)
):
    # Verify sender exists
    sender_name = None
    for name, id in users.items():
        if request.recipient_name == name:
            sender_name = name
            break

    if not sender_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": MessageStatus.UNAUTHORIZED,
                "message": "Invalid user ID"
            }
        )

    # Get recipient's ID from their username
    recipient_id = users.get(request.recipient_name)
    if not recipient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": MessageStatus.NOT_FOUND,
                "message": f"Recipient '{request.recipient_name}' not found"
            }
        )

    if recipient_id not in connections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": MessageStatus.NOT_FOUND,
                "message": f"Recipient '{request.recipient_name}' is not connected"
            }
        )
    
    message_id = str(uuid.uuid4())

    try:
        await connections[recipient_id].send_json({
            "to": sender_name,
            "message": request.message,
            "message_id": message_id,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        return SendMessageResponse(
            message_id=message_id,
            status=MessageStatus.DELIVERED,
            details=f"Message {message_id} delivered to {request.recipient_name}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": MessageStatus.INTERNAL_ERROR,
                "message": "Failed to deliver message",
                "error": str(e)
            }
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[Server] WebSocket connection accepted")
    user_id: Optional[str] = None
    try:
        # Attempt to get user_id from header
        user_id = websocket.headers.get("x-user-id")
        if user_id:
            # If header is provided, flush any duplicate auth message
            try:
                extra = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                try:
                    import json
                    data = json.loads(extra)
                    if "id" in data and data["id"] == user_id:
                        print("[Server] Duplicate auth message received and ignored")
                    else:
                        print(f"[Server] Received unexpected message during auth: {extra}")
                except Exception as parse_err:
                    print(f"[Server] Received non-JSON message during auth: {extra}")
            except asyncio.TimeoutError:
                pass
        else:
            # If header not provided, wait for authentication JSON message
            auth_data = await websocket.receive_json()
            user_id = auth_data.get("id")
        
        # Validate user_id
        if not user_id or not any(existing_id == user_id for existing_id in users.values()):
            await websocket.close(code=1008)
            return
        
        # Store connection
        connections[user_id] = websocket
        print(f"[Server] User with ID '{user_id}' connected")
        
        # Send connection acknowledgment
        await websocket.send_json({
            "type": "connection_status",
            "status": status.HTTP_101_SWITCHING_PROTOCOLS,
            "message": "Connected successfully"
        })
        
        # Keep connection alive and listen for messages
        while True:
            message = await websocket.receive_text()
            
            # Handle heartbeat
            if not message.strip():
                await websocket.send_json({
                    "type": "heartbeat",
                    "status": "ok"
                })
                continue
            
            # Handle other messages
            print(f"[Server] Received message from {user_id}: {message}")
    except WebSocketDisconnect:
        print(f"[Server] Connection disconnected for user '{user_id}'")
    except Exception as e:
        print(f"[Server] Error in WebSocket connection for user '{user_id}': {str(e)}")
    finally:
        if user_id in connections:
            del connections[user_id]
            print(f"[Server] Cleaned up connection for user '{user_id}'")

# New background task for periodic status logging
async def print_status_periodically():
    while True:
        print(f"[Status Update] Current users: {users}")
        print(f"[Status Update] Active WS connections: {list(connections.keys())}")
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(print_status_periodically())

if __name__ == "__main__":
    public_url = ngrok.connect(8000, "http")
    print(f"[Server] Public URL: {public_url}")
    print(f"[Server] WebSocket URL: {public_url}/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
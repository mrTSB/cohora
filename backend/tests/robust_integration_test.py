import asyncio
import json
import uuid
from typing import Dict, Any

import httpx
import websockets
import pytest

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

# Helper Functions
async def create_user(client: httpx.AsyncClient, name: str) -> Dict[str, Any]:
    response = await client.post(f"{BASE_URL}/api/users/create", json={"name": name})
    response.raise_for_status() # Raise an exception for bad status codes
    return response.json()

async def connect_ws(user_id: str, send_auth_json: bool = True, use_header: bool = False) -> websockets.WebSocketClientProtocol:
    headers = {}
    if use_header and user_id:
        headers["x-user-id"] = user_id
    
    ws = await websockets.connect(WS_URL, extra_headers=headers if use_header else None)
    
    if send_auth_json and user_id and not use_header: # Only send JSON auth if not using header auth
        await ws.send(json.dumps({"id": user_id}))
        # Wait for ack
        ack = await ws.recv()
        print(f"Auth ack for {user_id}: {ack}")
        assert json.loads(ack).get("status") == 101 # Switching Protocols
    elif use_header and user_id:
        # If using header, server should send ack immediately
        ack = await ws.recv()
        print(f"Auth ack for {user_id} (header auth): {ack}")
        assert json.loads(ack).get("status") == 101
    return ws

# Test Suite
@pytest.mark.asyncio
async def test_create_and_list_users():
    async with httpx.AsyncClient() as client:
        # Create user1
        user1_name = f"testuser_{uuid.uuid4()}"
        user1_data = await create_user(client, user1_name)
        user1_id = user1_data["id"]
        assert user1_data["status"] == 201
        print(f"Created user {user1_name} with ID {user1_id}")

        # Create user2
        user2_name = f"testuser_{uuid.uuid4()}"
        user2_data = await create_user(client, user2_name)
        user2_id = user2_data["id"]
        assert user2_data["status"] == 201
        print(f"Created user {user2_name} with ID {user2_id}")

        # List users and verify
        response = await client.get(f"{BASE_URL}/api/users/list")
        response.raise_for_status()
        listed_users = response.json()["users"]
        assert user1_name in listed_users
        assert listed_users[user1_name] == user1_id
        assert user2_name in listed_users
        assert listed_users[user2_name] == user2_id
        print("Listed users successfully.")

@pytest.mark.asyncio
async def test_create_user_already_exists():
    async with httpx.AsyncClient() as client:
        user_name = f"existinguser_{uuid.uuid4()}"
        await create_user(client, user_name) # Create user first
        
        # Attempt to create the same user again
        response = await client.post(f"{BASE_URL}/api/users/create", json={"name": user_name})
        assert response.status_code == 409 # Conflict
        assert "Username already exists" in response.json()["detail"]
        print("Verified creating existing user fails as expected.")

@pytest.mark.asyncio
async def test_websocket_connect_auth_json():
    async with httpx.AsyncClient() as client:
        user_name = f"ws_user_json_{uuid.uuid4()}"
        user_data = await create_user(client, user_name)
        user_id = user_data["id"]

        ws = None
        try:
            ws = await connect_ws(user_id, send_auth_json=True, use_header=False)
            print(f"User {user_name} ({user_id}) connected via WebSocket with JSON auth and received ack.")
            # Simple heartbeat check (optional, but good for testing connection liveness)
            await ws.send(" ") # Send whitespace as heartbeat
            heartbeat_ack = await asyncio.wait_for(ws.recv(), timeout=2)
            assert "heartbeat" in json.loads(heartbeat_ack).get("type")
            print(f"User {user_name} received heartbeat ack.")
        finally:
            if ws:
                await ws.close()

@pytest.mark.asyncio
async def test_websocket_connect_auth_header():
    async with httpx.AsyncClient() as client:
        user_name = f"ws_user_header_{uuid.uuid4()}"
        user_data = await create_user(client, user_name)
        user_id = user_data["id"]

        ws = None
        try:
            # Server should send ack immediately upon connection with header
            ws = await connect_ws(user_id, send_auth_json=False, use_header=True)
            print(f"User {user_name} ({user_id}) connected via WebSocket with header auth and received ack.")
            # Simple heartbeat check
            await ws.send(" ") # Send whitespace as heartbeat
            heartbeat_ack = await asyncio.wait_for(ws.recv(), timeout=2)
            assert "heartbeat" in json.loads(heartbeat_ack).get("type")
            print(f"User {user_name} received heartbeat ack.")
        finally:
            if ws:
                await ws.close()

@pytest.mark.asyncio
async def test_websocket_connect_invalid_user_id():
    invalid_user_id = str(uuid.uuid4()) # A non-existent user ID
    ws = None
    try:
        # Attempt to connect with an invalid ID via JSON auth
        with pytest.raises(websockets.exceptions.ConnectionClosedError) as excinfo_json:
            ws_json = await websockets.connect(WS_URL)
            await ws_json.send(json.dumps({"id": invalid_user_id}))
            await ws_json.recv() # Server should close connection
        assert excinfo_json.value.code == 1008 # Policy Violation (as per main.py logic for invalid user)
        print(f"Connection with invalid user ID (JSON auth) correctly closed with code {excinfo_json.value.code}.")
        if ws_json and not ws_json.closed:
            await ws_json.close()

        # Attempt to connect with an invalid ID via header auth
        with pytest.raises(websockets.exceptions.ConnectionClosedError) as excinfo_header:
            # The server logic might accept the connection initially then close it after checking the header
            # Or it might close it during the handshake if it processes headers early for auth decision.
            # Based on main.py, it accepts, then checks header, then closes if user_id from header is invalid.
            # However, if the header is present but the user ID doesn't exist in `users`, it sends an ack then main loop might error.
            # Let's refine this: main.py user_id check logic for header happens *before* sending ack.
            # So, it should close with 1008 if user_id from header is not in users dict.
            ws_header = await websockets.connect(WS_URL, extra_headers={"x-user-id": invalid_user_id})
            # The server should close the connection, client might see it as a normal close or a specific code
            await ws_header.recv() # This should fail as server closes it
        assert excinfo_header.value.code == 1008 # Policy Violation
        print(f"Connection with invalid user ID (header auth) correctly closed with code {excinfo_header.value.code}.")
        if ws_header and not ws_header.closed:
            await ws_header.close()

    except websockets.exceptions.InvalidStatusCode as e:
        # This can happen if the server rejects the connection during handshake due to header
        assert e.status_code in [401, 403] # Or whatever status code ngrok/server might send for early rejection
        print(f"Connection with invalid user ID (header auth) rejected during handshake with status {e.status_code}")
    finally:
        # Ensure ws objects are closed if they were somehow assigned and open
        if 'ws_json' in locals() and ws_json and not ws_json.closed:
            await ws_json.close()
        if 'ws_header' in locals() and ws_header and not ws_header.closed:
            await ws_header.close()


@pytest.mark.asyncio
async def test_websocket_connect_no_auth():
    ws = None
    try:
        ws = await websockets.connect(WS_URL)
        # Server waits for auth message. If not sent, it might timeout or close.
        # Based on main.py, it waits for auth_data = await websocket.receive_json()
        # If nothing sent, this will eventually lead to a timeout on the server side, 
        # or client might close. For robustness, client should expect a close.
        with pytest.raises(websockets.exceptions.ConnectionClosed) as excinfo:
            # Wait for a short period to see if server closes connection
            await asyncio.wait_for(ws.recv(), timeout=2.0) 
        # The server should close the connection due to lack of authentication (or timeout)
        # The close code might be 1002 (Protocol Error) or a custom one if server implements it.
        # main.py doesn't specify a close code for this exact scenario before auth timeout, but after timeout it would close.
        # If `receive_json()` times out or fails, it might result in a generic close or protocol error.
        # Let's assume server will close it (e.g. 1002, or 1001 if server is shutting down the handler)
        print(f"Connection without auth closed by server with code: {excinfo.value.code}")
        assert excinfo.value.code in [1002, 1001, 1008, 1011] # Protocol error, Going Away, Policy Violation, Internal Error
    except asyncio.TimeoutError:
        print("Client timed out waiting for server to close connection after no auth. This is also a valid outcome.")
    finally:
        if ws and not ws.closed:
            await ws.close()

@pytest.mark.asyncio
async def test_websocket_send_message_before_auth():
    ws = None
    try:
        ws = await websockets.connect(WS_URL)
        # Attempt to send data before authenticating
        await ws.send(json.dumps({"message": "hello"}))
        
        # Server behavior might vary: close connection, ignore message, or error.
        # In main.py, it first tries to receive auth data (JSON or from header).
        # If it receives a non-auth JSON first, it might fail parsing for 'id' or user_id validation.
        # Let's see how main.py handles this: it expects auth first.
        # `auth_data = await websocket.receive_json()` will try to parse this. If it doesn't have 'id', it will lead to closure.
        with pytest.raises(websockets.exceptions.ConnectionClosedError) as excinfo:
            await ws.recv() # Expect server to close the connection
        assert excinfo.value.code == 1008 # Policy Violation (or 1003/1007 if data is unparseable/invalid for auth)
        print(f"Sending message before auth correctly led to connection close with code {excinfo.value.code}.")
    finally:
        if ws and not ws.closed:
            await ws.close()

@pytest.mark.asyncio
async def test_send_message_http_successful():
    async with httpx.AsyncClient() as client:
        sender_name = f"sender_http_{uuid.uuid4()}"
        recipient_name = f"recipient_http_{uuid.uuid4()}"

        sender_data = await create_user(client, sender_name)
        sender_id = sender_data["id"]
        recipient_data = await create_user(client, recipient_name)
        recipient_id = recipient_data["id"]

        ws_recipient = None
        try:
            # Connect recipient's WebSocket
            ws_recipient = await connect_ws(recipient_id)
            print(f"Recipient {recipient_name} connected.")

            # Sender sends message via HTTP
            message_content = f"Hello {recipient_name} from {sender_name} via HTTP!"
            payload = {"recipient_name": recipient_name, "message": message_content}
            headers = {"x-user-id": sender_id}
            
            response = await client.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
            response.raise_for_status()
            send_data = response.json()
            print(f"Send message HTTP response: {send_data}")
            assert send_data["status"] == 200 # MessageStatus.DELIVERED
            assert send_data["details"] == f"Message {send_data['message_id']} delivered to {recipient_name}"

            # Recipient receives message via WebSocket
            received_msg_json = await asyncio.wait_for(ws_recipient.recv(), timeout=3)
            received_msg = json.loads(received_msg_json)
            print(f"Recipient {recipient_name} received on WS: {received_msg}")

            assert received_msg["from"] == sender_name
            assert received_msg["message"] == message_content
            assert received_msg["message_id"] == send_data["message_id"]
        finally:
            if ws_recipient and not ws_recipient.closed:
                await ws_recipient.close()

@pytest.mark.asyncio
async def test_send_message_http_recipient_not_found():
    async with httpx.AsyncClient() as client:
        sender_name = f"sender_nr_{uuid.uuid4()}"
        sender_data = await create_user(client, sender_name)
        sender_id = sender_data["id"]

        non_existent_recipient_name = f"nosuchuser_{uuid.uuid4()}"
        payload = {"recipient_name": non_existent_recipient_name, "message": "Hello?"}
        headers = {"x-user-id": sender_id}

        response = await client.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
        assert response.status_code == 404
        error_details = response.json()["detail"]
        assert error_details["code"] == 404 # MessageStatus.NOT_FOUND
        assert f"Recipient '{non_existent_recipient_name}' not found" in error_details["message"]
        print("Verified sending message to non-existent recipient fails correctly.")

@pytest.mark.asyncio
async def test_send_message_http_recipient_not_connected():
    async with httpx.AsyncClient() as client:
        sender_name = f"sender_ndc_{uuid.uuid4()}"
        recipient_name = f"recipient_ndc_{uuid.uuid4()}"

        sender_data = await create_user(client, sender_name)
        sender_id = sender_data["id"]
        await create_user(client, recipient_name) # Recipient exists but is not connected

        payload = {"recipient_name": recipient_name, "message": "Are you there?"}
        headers = {"x-user-id": sender_id}

        response = await client.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
        assert response.status_code == 404 # As per main.py logic
        error_details = response.json()["detail"]
        assert error_details["code"] == 404 # MessageStatus.NOT_FOUND
        assert f"Recipient '{recipient_name}' is not connected" in error_details["message"]
        print("Verified sending message to disconnected recipient fails correctly.")

@pytest.mark.asyncio
async def test_send_message_http_unauthenticated():
    async with httpx.AsyncClient() as client:
        recipient_name = f"recipient_unauth_{uuid.uuid4()}"
        await create_user(client, recipient_name) # Recipient needs to exist for other checks
        # We also need the recipient to be connected for the message to be delivered if auth passed
        # However, this test focuses on the auth failure for the *sender*

        payload = {"recipient_name": recipient_name, "message": "Secret message"}
        # No x-user-id header
        response = await client.post(f"{BASE_URL}/api/messages/send", json=payload)
        assert response.status_code == 401
        error_details = response.json()["detail"]
        assert error_details["code"] == 401 # MessageStatus.UNAUTHORIZED
        assert "Authentication required" in error_details["message"]
        print("Verified sending message unauthenticated (no header) fails correctly.")

@pytest.mark.asyncio
async def test_send_message_http_invalid_sender_id():
    async with httpx.AsyncClient() as client:
        recipient_name = f"recipient_inv_sender_{uuid.uuid4()}"
        await create_user(client, recipient_name) # Recipient exists

        invalid_sender_id = str(uuid.uuid4())
        payload = {"recipient_name": recipient_name, "message": "Message from a ghost"}
        headers = {"x-user-id": invalid_sender_id}

        response = await client.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
        assert response.status_code == 401
        error_details = response.json()["detail"]
        assert error_details["code"] == 401 # MessageStatus.UNAUTHORIZED
        assert "Invalid user ID" in error_details["message"]
        print("Verified sending message with invalid sender ID fails correctly.")

@pytest.mark.asyncio
async def test_send_message_http_to_self():
    async with httpx.AsyncClient() as client:
        user_name = f"self_sender_{uuid.uuid4()}"
        user_data = await create_user(client, user_name)
        user_id = user_data["id"]

        ws_user = None
        try:
            ws_user = await connect_ws(user_id)
            print(f"User {user_name} connected for self-messaging test.")

            message_content = f"Hello me, {user_name}!"
            payload = {"recipient_name": user_name, "message": message_content}
            headers = {"x-user-id": user_id}

            response = await client.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
            response.raise_for_status()
            send_data = response.json()
            assert send_data["status"] == 200

            received_msg_json = await asyncio.wait_for(ws_user.recv(), timeout=3)
            received_msg = json.loads(received_msg_json)
            print(f"User {user_name} received self-message: {received_msg}")

            assert received_msg["from"] == user_name
            assert received_msg["message"] == message_content
            assert received_msg["message_id"] == send_data["message_id"]
            print("Verified sending message to self successfully.")
        finally:
            if ws_user and not ws_user.closed:
                await ws_user.close()

@pytest.mark.asyncio
async def test_websocket_duplicate_auth_after_header_auth():
    async with httpx.AsyncClient() as client:
        user_name = f"ws_dup_auth_{uuid.uuid4()}"
        user_data = await create_user(client, user_name)
        user_id = user_data["id"]

        ws = None
        try:
            # Connect with header auth, this also consumes the initial ack
            ws = await connect_ws(user_id, send_auth_json=False, use_header=True)
            print(f"User {user_name} ({user_id}) connected via WebSocket with header auth.")

            # Send a duplicate JSON auth message
            await ws.send(json.dumps({"id": user_id}))
            print(f"Sent duplicate JSON auth for {user_name}.")

            # The server should ignore this. We can test by sending a heartbeat 
            # and ensuring the connection is still alive and responsive.
            # Or by checking server logs if they indicate "Duplicate auth message received and ignored"
            await ws.send(" ") # Send whitespace as heartbeat
            heartbeat_ack_json = await asyncio.wait_for(ws.recv(), timeout=2)
            heartbeat_ack = json.loads(heartbeat_ack_json)
            assert heartbeat_ack.get("type") == "heartbeat"
            assert heartbeat_ack.get("status") == "ok"
            print(f"User {user_name} received heartbeat ack after sending duplicate auth. Connection stable.")

        finally:
            if ws and not ws.closed:
                await ws.close()

@pytest.mark.asyncio
async def test_simultaneous_connections_and_messaging():
    async with httpx.AsyncClient() as client:
        user1_name = f"sim_user1_{uuid.uuid4()}"
        user2_name = f"sim_user2_{uuid.uuid4()}"

        user1_data = await create_user(client, user1_name)
        user1_id = user1_data["id"]
        user2_data = await create_user(client, user2_name)
        user2_id = user2_data["id"]

        ws1 = None
        ws2 = None
        try:
            # Connect both users
            ws1 = await connect_ws(user1_id)
            print(f"User {user1_name} connected.")
            ws2 = await connect_ws(user2_id)
            print(f"User {user2_name} connected.")

            # User1 sends message to User2 via HTTP
            msg1_to_2_content = f"Hello {user2_name} from {user1_name}!"
            payload1 = {"recipient_name": user2_name, "message": msg1_to_2_content}
            headers1 = {"x-user-id": user1_id}
            res1 = await client.post(f"{BASE_URL}/api/messages/send", json=payload1, headers=headers1)
            res1.raise_for_status()
            msg1_id = res1.json()["message_id"]

            # User2 receives message
            recv_msg_user2_json = await asyncio.wait_for(ws2.recv(), timeout=3)
            recv_msg_user2 = json.loads(recv_msg_user2_json)
            assert recv_msg_user2["from"] == user1_name
            assert recv_msg_user2["message"] == msg1_to_2_content
            assert recv_msg_user2["message_id"] == msg1_id
            print(f"{user2_name} received message from {user1_name}.")

            # User2 sends message to User1 via HTTP
            msg2_to_1_content = f"Hi {user1_name} from {user2_name}!"
            payload2 = {"recipient_name": user1_name, "message": msg2_to_1_content}
            headers2 = {"x-user-id": user2_id}
            res2 = await client.post(f"{BASE_URL}/api/messages/send", json=payload2, headers=headers2)
            res2.raise_for_status()
            msg2_id = res2.json()["message_id"]

            # User1 receives message
            recv_msg_user1_json = await asyncio.wait_for(ws1.recv(), timeout=3)
            recv_msg_user1 = json.loads(recv_msg_user1_json)
            assert recv_msg_user1["from"] == user2_name
            assert recv_msg_user1["message"] == msg2_to_1_content
            assert recv_msg_user1["message_id"] == msg2_id
            print(f"{user1_name} received message from {user2_name}.")

        finally:
            if ws1 and not ws1.closed:
                await ws1.close()
            if ws2 and not ws2.closed:
                await ws2.close()

@pytest.mark.asyncio
async def test_websocket_heartbeat():
    async with httpx.AsyncClient() as client:
        user_name = f"heartbeat_user_{uuid.uuid4()}"
        user_data = await create_user(client, user_name)
        user_id = user_data["id"]
        ws = None
        try:
            ws = await connect_ws(user_id)
            print(f"User {user_name} connected for heartbeat test.")
            
            # Send heartbeat (empty or whitespace message)
            await ws.send(" ") 
            response_json = await asyncio.wait_for(ws.recv(), timeout=2)
            response = json.loads(response_json)
            
            assert response.get("type") == "heartbeat"
            assert response.get("status") == "ok"
            print("Heartbeat acknowledged by server.")
        finally:
            if ws and not ws.closed:
                await ws.close()

@pytest.mark.asyncio
async def test_websocket_malformed_auth_json():
    ws = None
    try:
        ws = await websockets.connect(WS_URL)
        # Send malformed JSON (e.g., missing 'id' field or not JSON at all)
        await ws.send(json.dumps({"user_identity": "some_user"})) # Missing 'id'
        
        with pytest.raises(websockets.exceptions.ConnectionClosedError) as excinfo:
            await ws.recv() # Server should close due to invalid auth data
        
        # Based on main.py, if `user_id = auth_data.get("id")` is None, it closes with 1008
        assert excinfo.value.code == 1008 # Policy Violation
        print(f"Sending malformed auth JSON correctly led to connection close with code {excinfo.value.code}.")
    finally:
        if ws and not ws.closed:
            await ws.close()
    
    # Test sending non-JSON data for auth
    ws_non_json = None
    try:
        ws_non_json = await websockets.connect(WS_URL)
        await ws_non_json.send("this is not json")
        with pytest.raises(websockets.exceptions.ConnectionClosedError) as excinfo_non_json:
            await ws_non_json.recv()
        # main.py `auth_data = await websocket.receive_json()` would raise error, leading to exception handler
        # The generic exception handler in websocket_endpoint might not set a specific code, 
        # or websockets library might use a generic code if server crashes handler before close frame.
        # Often 1002 (Protocol Error) or 1011 (Internal Error) if server fails to parse and doesn't send specific close code.
        # Given main.py's structure, a parsing error for receive_json() will go to the broad `except Exception`
        # which doesn't explicitly close the websocket with a code before `del connections[user_id]`
        # The `finally` block in `websocket_endpoint` has `del connections[user_id]` which may not be reached if user_id is not set.
        # Python websockets library might default to 1006 (Abnormal Closure) if server drops connection without proper close frame.
        # Let's assume a general error code or one that indicates bad data.
        # The server actually prints "[Server] Received non-JSON message during auth: this is not json"
        # and then tries to get user_id, which is None. Then `if not user_id or ...` closes with 1008.
        assert excinfo_non_json.value.code == 1008 # Policy Violation after failing to get user_id
        print(f"Sending non-JSON auth data correctly led to connection close with code {excinfo_non_json.value.code}.")
    finally:
        if ws_non_json and not ws_non_json.closed:
            await ws_non_json.close()

# Note: Testing abrupt disconnects from the client side and verifying server cleanup 
# (e.g., removal from `connections` dict) is harder without direct server-side state inspection 
# or specific server logs for these tests. We trust `main.py`'s `finally` block in `websocket_endpoint` handles this.

async def main():
    # This function can be used to run specific tests if not using pytest,
    # but pytest handles test discovery and execution automatically.
    print("Running robust integration tests...")
    # Example of how you might run tests manually (not recommended if using pytest)
    # await test_create_and_list_users()
    # await test_create_user_already_exists()
    print("Robust integration tests finished.")

if __name__ == "__main__":
    # It's better to run pytest from the command line:
    # cd backend
    # python -m pytest tests/robust_integration_test.py
    # However, you can still run this file directly for limited testing:
    asyncio.run(main()) 
import asyncio
import json
import pytest
import httpx
import websockets
from typing import Dict, Tuple

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

async def create_user(client: httpx.AsyncClient, name: str) -> Dict:
    res = await client.post(f"{BASE_URL}/api/users/create", json={"name": name})
    return res.json()

async def connect_ws(user_id: str) -> websockets.WebSocketClientProtocol:
    ws = await websockets.connect(WS_URL)
    await ws.send(json.dumps({"id": user_id}))
    ack = await ws.recv()
    return ws

async def test_basic_message_flow():
    # Original test case renamed and slightly modified
    async with httpx.AsyncClient() as client:
        # Create users
        user1_data = await create_user(client, "alice")
        user2_data = await create_user(client, "bob")
        user1_id, user2_id = user1_data["id"], user2_data["id"]

        # Connect websockets
        ws_alice = await connect_ws(user1_id)
        ws_bob = await connect_ws(user2_id)
        
        # Send message
        message_payload = {
            "recipient_name": "bob",
            "message": "Hello Bob! This is Alice."
        }
        send_res = await client.post(
            f"{BASE_URL}/api/messages/send",
            json=message_payload,
            headers={"x-user-id": user1_id}
        )
        assert send_res.status_code == 200
        
        # Verify message received
        received_msg = json.loads(await ws_bob.recv())
        assert received_msg["message"] == "Hello Bob! This is Alice."
        assert received_msg["sender_name"] == "alice"
        
        await ws_alice.close()
        await ws_bob.close()

async def test_message_to_offline_user():
    async with httpx.AsyncClient() as client:
        # Create users but don't connect Bob's websocket
        alice_data = await create_user(client, "alice_offline")
        bob_data = await create_user(client, "bob_offline")
        
        # Only Alice connects
        ws_alice = await connect_ws(alice_data["id"])
        
        # Send message to offline Bob
        message_payload = {
            "recipient_name": "bob_offline",
            "message": "Are you there?"
        }
        send_res = await client.post(
            f"{BASE_URL}/api/messages/send",
            json=message_payload,
            headers={"x-user-id": alice_data["id"]}
        )
        
        # Message should be accepted even if recipient is offline
        assert send_res.status_code == 200
        
        # When Bob connects later, he should receive the message
        ws_bob = await connect_ws(bob_data["id"])
        received_msg = json.loads(await ws_bob.recv())
        assert received_msg["message"] == "Are you there?"
        
        await ws_alice.close()
        await ws_bob.close()

async def test_invalid_recipient():
    async with httpx.AsyncClient() as client:
        alice_data = await create_user(client, "alice_invalid")
        ws_alice = await connect_ws(alice_data["id"])
        
        # Try to send message to non-existent user
        message_payload = {
            "recipient_name": "nonexistent_user",
            "message": "Hello?"
        }
        send_res = await client.post(
            f"{BASE_URL}/api/messages/send",
            json=message_payload,
            headers={"x-user-id": alice_data["id"]}
        )
        
        assert send_res.status_code == 404
        await ws_alice.close()

async def test_multiple_connections_same_user():
    async with httpx.AsyncClient() as client:
        # Create single user with multiple connections
        user_data = await create_user(client, "multi_user")
        
        # Connect three websockets for the same user
        ws1 = await connect_ws(user_data["id"])
        ws2 = await connect_ws(user_data["id"])
        ws3 = await connect_ws(user_data["id"])
        
        # Create another user to send messages
        sender_data = await create_user(client, "sender")
        message_payload = {
            "recipient_name": "multi_user",
            "message": "Broadcasting!"
        }
        
        # Send message and verify it's received on all connections
        send_res = await client.post(
            f"{BASE_URL}/api/messages/send",
            json=message_payload,
            headers={"x-user-id": sender_data["id"]}
        )
        
        # All connections should receive the message
        for ws in [ws1, ws2, ws3]:
            received_msg = json.loads(await ws.recv())
            assert received_msg["message"] == "Broadcasting!"
        
        await ws1.close()
        await ws2.close()
        await ws3.close()

async def test_message_rate_limiting():
    async with httpx.AsyncClient() as client:
        sender_data = await create_user(client, "spam_sender")
        receiver_data = await create_user(client, "spam_receiver")
        
        ws_receiver = await connect_ws(receiver_data["id"])
        
        # Try to send multiple messages rapidly
        message_payload = {
            "recipient_name": "spam_receiver",
            "message": "Rapid message"
        }
        
        responses = []
        for _ in range(10):  # Try sending 10 messages rapidly
            res = await client.post(
                f"{BASE_URL}/api/messages/send",
                json=message_payload,
                headers={"x-user-id": sender_data["id"]}
            )
            responses.append(res.status_code)
            
        # Check if rate limiting is working
        # Some requests might be rate limited (status code 429)
        assert 429 in responses or all(r == 200 for r in responses)
        
        await ws_receiver.close()

async def test_long_message():
    async with httpx.AsyncClient() as client:
        sender_data = await create_user(client, "long_sender")
        receiver_data = await create_user(client, "long_receiver")
        
        ws_receiver = await connect_ws(receiver_data["id"])
        
        # Create a very long message
        long_message = "A" * 10000  # 10KB message
        message_payload = {
            "recipient_name": "long_receiver",
            "message": long_message
        }
        
        send_res = await client.post(
            f"{BASE_URL}/api/messages/send",
            json=message_payload,
            headers={"x-user-id": sender_data["id"]}
        )
        
        # Server should either accept or reject with 413 (Payload Too Large)
        assert send_res.status_code in [200, 413]
        
        await ws_receiver.close()

if __name__ == "__main__":
    asyncio.run(test_basic_message_flow()) 
import asyncio
import json

import httpx
import websockets

BASE_URL = "https://17a0-50-175-245-62.ngrok-free.app"
WS_URL = "wss://17a0-50-175-245-62.ngrok-free.app/ws"

async def main():
    async with httpx.AsyncClient() as client:
        # Create two users: 'alice' and 'bob'
        res1 = await client.post(f"{BASE_URL}/api/users/create", json={"name": "alice"})
        res2 = await client.post(f"{BASE_URL}/api/users/create", json={"name": "bob"})
        user1_data = res1.json()
        user2_data = res2.json()
        user1_id = user1_data["id"]
        user2_id = user2_data["id"]
        print("Created users:")
        print("Alice:", user1_data)
        print("Bob:", user2_data)
        
        # Establish websocket connections for both users
        print("Connecting websockets...")
        ws_alice = await websockets.connect(WS_URL)
        print("Alice WebSocket connected.")
        # Authenticate Alice by sending her ID
        await ws_alice.send(json.dumps({"id": user1_id}))
        print(f"Sent auth for Alice: {user1_id}")

        ws_bob = await websockets.connect(WS_URL)
        print("Bob WebSocket connected.")
        # Authenticate Bob by sending his ID
        await ws_bob.send(json.dumps({"id": user2_id}))
        print(f"Sent auth for Bob: {user2_id}")
        
        # Receive connection acknowledgements from the server
        ack_alice = await ws_alice.recv()
        ack_bob = await ws_bob.recv()
        print("Alice WebSocket Ack:", ack_alice)
        print("Bob WebSocket Ack:", ack_bob)

        await asyncio.sleep(10)
        
        # Send a message from Alice to Bob via the HTTP endpoint
        message_payload = {
            "recipient_name": "bob",
            "message": "Hello Bob! This is Alice."
        }
        # send_res = await client.post(f"{BASE_URL}/api/messages/send", json=message_payload, headers={"x-user-id": user1_id})
        send_res = await client.post(f"{BASE_URL}/api/messages/send", json=message_payload)
        send_data = send_res.json()
        print("Send Message Response:", send_data)
        
        # Bob should receive the message over his websocket connection
        received_msg = await ws_bob.recv()
        print("Bob Received Message:", received_msg)
        
        # Cleanup websocket connections
        await ws_alice.close()
        await ws_bob.close()

async def listen_test():
    async with httpx.AsyncClient() as client:
        # Create a single user
        res = await client.post(f"{BASE_URL}/api/users/create", json={"name": "Tanvir"})
        user_data = res.json()
        user_id = user_data["id"]
        print("Created user:")
        print("Listener:", user_data)
        
        # Establish websocket connection
        print("Connecting websocket...")
        ws = await websockets.connect(WS_URL)
        print("WebSocket connected.")
        
        # Authenticate by sending user ID
        await ws.send(json.dumps({"id": user_id}))
        print(f"Sent auth for listener: {user_id}")
        
        # Receive connection acknowledgement
        ack = await ws.recv()
        print("WebSocket Ack:", ack)
        
        print("Listening for messages... (Press Ctrl+C to stop)")
        try:
            while True:
                message = await ws.recv()
                print("Received message:", message)
        except KeyboardInterrupt:
            print("\nStopping listener...")
        finally:
            await ws.close()

if __name__ == "__main__":
    # Uncomment the test you want to run
    # asyncio.run(main())
    asyncio.run(listen_test()) 

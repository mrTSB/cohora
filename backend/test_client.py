import asyncio
import websockets
import json
import requests
import sys
from datetime import datetime

class ChatClient:
    def __init__(self, base_url, ws_url):
        self.base_url = base_url
        self.ws_url = ws_url
        self.user_id = None
        self.username = None
        self.ws = None

    async def register(self, username):
        """Register a new user"""
        response = requests.post(
            f"{self.base_url}/api/users/create",
            json={"name": username}
        )
        if response.status_code == 201:
            self.user_id = response.json()["id"]
            self.username = username
            print(f"Registered successfully! User ID: {self.user_id}")
            return True
        else:
            print(f"Registration failed: {response.text}")
            return False

    async def connect_websocket(self):
        """Connect to the WebSocket server"""
        try:
            self.ws = await websockets.connect(self.ws_url)
            # Send authentication
            await self.ws.send(json.dumps({"id": self.user_id}))
            response = await self.ws.recv()
            print(f"WebSocket connected: {response}")
            return True
        except Exception as e:
            print(f"WebSocket connection failed: {e}")
            return False

    async def send_message(self, recipient_name, message):
        """Send a message to another user"""
        response = requests.post(
            f"{self.base_url}/api/messages/send",
            headers={"X-User-ID": self.user_id},
            json={
                "recipient_name": recipient_name,
                "message": message
            }
        )
        print(f"Message send response: {response.text}")

    async def receive_messages(self):
        """Receive messages"""
        try:
            while True:
                message = await self.ws.recv()
                try:
                    data = json.loads(message)
                    # Check if this is a message or connection status
                    if "type" in data and data["type"] == "connection_status":
                        print(f"\nConnection status: {data['message']}")
                    else:
                        timestamp = datetime.fromtimestamp(data["timestamp"]).strftime('%H:%M:%S')
                        print(f"\n\n=== New Message ===")
                        print(f"From: {data['from']}")
                        print(f"Time: {timestamp}")
                        print(f"Message: {data['message']}")
                        print("=================")
                        print("\nEnter message (recipient message): ", end='', flush=True)
                except json.JSONDecodeError:
                    # This might be a heartbeat response
                    continue
                except Exception as e:
                    print(f"\nError processing message: {e}")
                    print("Raw message:", message)
                    print("\nEnter message (recipient message): ", end='', flush=True)
        except websockets.exceptions.ConnectionClosed:
            print("\nConnection closed")

    async def heartbeat(self):
        """Send periodic heartbeat to keep connection alive"""
        try:
            while True:
                await self.ws.send("")  # Empty message as heartbeat
                await asyncio.sleep(5)  # Send heartbeat every 5 seconds
        except websockets.exceptions.ConnectionClosed:
            print("Heartbeat: Connection closed")

    async def run(self):
        """Main loop for sending messages"""
        try:
            print("Enter messages in format: recipient_name message")
            print("Example: Alice Hello there!")
            print("Enter 'quit' to exit")
            
            # Start heartbeat in the background
            heartbeat_task = asyncio.create_task(self.heartbeat())
            
            while True:
                try:
                    user_input = input("Enter message (recipient message): ")
                    if user_input.lower() == 'quit':
                        break

                    # Split input into recipient and message
                    parts = user_input.split(' ', 1)
                    if len(parts) != 2:
                        print("Invalid format. Use: recipient_name message")
                        continue

                    recipient, message = parts
                    await self.send_message(recipient, message)
                except Exception as e:
                    print(f"Error sending message: {e}")

        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            if self.ws:
                await self.ws.close()
            # Cancel heartbeat task
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

async def main():
    if len(sys.argv) != 2:
        print("Usage: python test_client.py <username>")
        return

    username = sys.argv[1]
    
    # Using the ngrok URLs
    base_url = "https://829b-50-175-245-62.ngrok-free.app"
    ws_url = "wss://829b-50-175-245-62.ngrok-free.app/ws"
    
    print(f"Connecting to server at {base_url}")
    print(f"WebSocket URL: {ws_url}")

    client = ChatClient(base_url, ws_url)
    
    # Register and connect
    if await client.register(username):
        if await client.connect_websocket():
            # Start receiving messages in the background
            asyncio.create_task(client.receive_messages())
            # Run the main loop for sending messages
            await client.run()

if __name__ == "__main__":
    asyncio.run(main()) 
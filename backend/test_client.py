import asyncio
import websockets
import json
import requests
import sys
from datetime import datetime
import logging
import ssl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatClient:
    def __init__(self, base_url, ws_url):
        self.base_url = base_url
        self.ws_url = ws_url
        self.user_id = None
        self.username = None
        self.ws = None
        self.connected = False
        self.should_reconnect = True
        self.last_status_check = 0

    async def register(self, username):
        """Register a new user"""
        try:
            response = requests.post(
                f"{self.base_url}/api/users/create",
                json={"name": username}
            )
            if response.status_code == 201:
                self.user_id = response.json()["id"]
                self.username = username
                logger.info(f"Registered successfully! User ID: {self.user_id}")
                return True
            else:
                logger.error(f"Registration failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            return False

    async def connect_websocket(self):
        """Connect to the WebSocket server"""
        while True:  # Keep trying forever
            try:
                if self.ws:
                    try:
                        await self.ws.close()
                    except:
                        pass
                
                logger.info("Attempting to connect to WebSocket...")
                
                headers = {"X-User-ID": self.user_id} if self.user_id else {}
                ssl_context = ssl._create_unverified_context()
                self.ws = await websockets.connect(
                    self.ws_url,
                    ping_interval=None,  # We'll handle our own heartbeat
                    ping_timeout=None,   # Disable built-in ping timeout
                    close_timeout=None,  # Never timeout on close
                    max_size=10_000_000, # 10MB max message size
                    extra_headers=headers,
                    ssl=ssl_context
                )
                
                if headers:
                    logger.info("Authentication via header used; skipping auth message")
                else:
                    auth_data = {"id": self.user_id}
                    logger.info(f"Sending authentication: {auth_data}")
                    await self.ws.send(json.dumps(auth_data))
                
                # Wait for auth response
                response = await self.ws.recv()
                response_data = json.loads(response)
                
                if response_data.get("type") == "connection_status":
                    logger.info(f"WebSocket connected: {response_data['message']}")
                    self.connected = True
                    return True
                    
            except Exception as e:
                logger.error(f"Connection attempt failed: {e}")
                self.connected = False
                await asyncio.sleep(2)  # Wait briefly before retry
                continue

    async def send_message(self, recipient_name, message):
        """Send a message to another user"""
        try:
            response = requests.post(
                f"{self.base_url}/api/messages/send",
                headers={"X-User-ID": self.user_id},
                json={
                    "recipient_name": recipient_name,
                    "message": message
                }
            )
            if response.status_code == 200:
                logger.info("Message sent successfully")
            else:
                logger.error(f"Failed to send message: {response.text}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def receive_messages(self):
        """Receive messages"""
        while True:  # Never stop receiving
            if not self.ws or not self.connected:
                await self.connect_websocket()
                continue

            try:
                message = await self.ws.recv()
                try:
                    data = json.loads(message)
                    if "type" in data and data["type"] == "connection_status":
                        logger.info(f"Connection status: {data['message']}")
                    elif "type" in data and data["type"] == "heartbeat":
                        continue  # Skip heartbeat messages
                    elif message.strip():  # Only process non-empty messages
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"\n\n=== New Message ===")
                        print(f"From: {data['from']}")
                        print(f"Time: {timestamp}")
                        print(f"Message: {data['message']}")
                        print("=================")
                        print("\nEnter message (recipient message): ", end='', flush=True)
                except json.JSONDecodeError:
                    # Not a JSON message
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
            except Exception as e:
                logger.warning(f"Receive error, reconnecting: {e}")
                self.connected = False
                await asyncio.sleep(1)

    async def heartbeat(self):
        """Send periodic heartbeat to keep connection alive"""
        while True:  # Never stop heartbeat
            try:
                if self.ws and self.connected:
                    await self.ws.send("")
                    try:
                        response = await self.ws.recv()
                        try:
                            data = json.loads(response)
                            if data.get("type") == "heartbeat":
                                logger.debug("Heartbeat ok")
                        except json.JSONDecodeError:
                            # Might be a regular message
                            pass
                    except Exception as e:
                        logger.warning(f"Heartbeat response error: {e}")
                        self.connected = False
                
                await asyncio.sleep(15)  # Heartbeat every 15 seconds
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                self.connected = False
                await asyncio.sleep(1)

    async def check_connection_status(self):
        """Regularly check and report WebSocket connection status"""
        last_status = None
        while True:  # Never stop checking
            try:
                current_status = "CONNECTED" if self.ws and self.connected else "RECONNECTING..."
                current_time = datetime.now().strftime('%H:%M:%S')
                
                if current_status != last_status:
                    if current_status == "CONNECTED":
                        print(f"\n[{current_time}] WebSocket: ✓ CONNECTED")
                    else:
                        print(f"\n[{current_time}] WebSocket: ⟳ RECONNECTING...")
                
                last_status = current_status
                
            except Exception as e:
                logger.error(f"Status check error: {e}")
                
            await asyncio.sleep(5)  # Check every 5 seconds

    async def run(self):
        """Main loop for sending messages"""
        try:
            print("\nChat Client Started")
            print("===================")
            print("Enter messages in format: recipient_name message")
            print("Example: Alice Hello there!")
            print("Enter 'quit' to exit")
            print("===================\n")
            
            # Start background tasks
            tasks = [
                asyncio.create_task(self.heartbeat()),
                asyncio.create_task(self.receive_messages()),
                asyncio.create_task(self.check_connection_status())
            ]
            
            while True:
                try:
                    user_input = input("\nEnter message (recipient message): ")
                    if user_input.lower() == 'quit':
                        break

                    parts = user_input.split(' ', 1)
                    if len(parts) != 2:
                        print("Invalid format. Use: recipient_name message")
                        continue

                    recipient, message = parts
                    await self.send_message(recipient, message)
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")

        except KeyboardInterrupt:
            logger.info("\nExiting...")
        finally:
            # Cancel all background tasks
            for task in tasks:
                task.cancel()
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                pass
            
            if self.ws:
                await self.ws.close()

async def main():
    if len(sys.argv) != 2:
        print("Usage: python test_client.py <username>")
        return

    username = sys.argv[1]
    
    # Using the ngrok URLs
    base_url = "https://539d-50-175-245-62.ngrok-free.app"
    ws_url = "https://539d-50-175-245-62.ngrok-free.app"
    
    print(f"Connecting to server at {base_url}")
    print(f"WebSocket URL: {ws_url}")

    client = ChatClient(base_url, ws_url)
    
    # Register and connect
    if await client.register(username):
        await client.run()  # This will handle connection and reconnection

if __name__ == "__main__":
    asyncio.run(main()) 
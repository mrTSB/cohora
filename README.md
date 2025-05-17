# cohora

Chat Server API - Specification and Behavior

Overview:
This server provides basic user management and real-time messaging via REST endpoints and WebSocket communication. Clients can register users, list all users, send messages by user ID, and receive messages in real-time through WebSocket connections.

Endpoints:

Create User
POST /api/users/create
Registers a new user using a unique name and returns a generated user ID.
Request: { "name": "Alice" }
Response: { "id": "uuid-1234" }
If the name is already taken, respond with 409 Conflict.

List Users
GET /api/users/list
Returns a dictionary of all registered users.
Response: { "users": { "Alice": "uuid-1234", "Bob": "uuid-5678" } }

Send Message
POST /api/messages/send
Sends a message to another user using their ID. The recipient must be connected via WebSocket to receive it in real time.
Request: { "recipient_id": "uuid-5678", "message": "Hello, Bob!" }
Response: { "status": "success", "details": "Message sent to recipient_id: uuid-5678" }

WebSocket Protocol:

Connection
Clients connect to ws://<server>/ws and must immediately send their user ID to authenticate:
{ "id": "uuid-1234" }
After successful authentication, the client begins listening for incoming messages.

Incoming Messages (from server to client)
Messages pushed by the server follow this format:
{ "from": "Alice", "message": "Hey there!" }
Clients should append these to the chat history upon receipt.

Client Modes:

Listening Mode
Client connects to WebSocket and passively receives messages in real time. Messages are added to the user’s chat history as they arrive.

Chatting Mode
Client sends messages via REST while potentially maintaining an open WebSocket for incoming replies. This mode enables two-way real-time chat.

Example Flow:

Alice registers with POST /api/users/create and receives an ID.

She connects to the WebSocket and authenticates.

Bob does the same.

Alice sends a message using POST /api/messages/send with Bob’s ID.

Bob receives the message immediately through the WebSocket.

Error Handling:

400 Bad Request – Invalid or missing input
401 Unauthorized – Invalid or missing ID on WebSocket connect
404 Not Found – Recipient ID does not exist
409 Conflict – Username already exists
500 Internal Server Error – Unexpected failure

Contact the backend team for questions or integration support.
import { BASE_URL, WS_URL } from "@/lib/config";

// Represents the status of a message
enum MessageStatus {
  DELIVERED = 200,
  QUEUED = 202,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  NOT_FOUND = 404,
  INTERNAL_ERROR = 500,
}

// Types for API requests and responses
interface CreateUserRequest {
  name: string;
}

interface CreateUserResponse {
  id: string;
  status: number;
}

interface SendMessageRequest {
  recipient_name: string;
  message: string;
}

interface SendMessageResponse {
  message_id: string;
  status: MessageStatus;
  details: string;
}

interface MessageDelivery {
  from: string;
  message: string;
  timestamp: number;
  message_id: string;
}

export type { MessageDelivery };

let userId: string | null = null;
let ws: WebSocket | null = null;
let messageCallback: ((message: MessageDelivery) => void) | null = null;

// Create a new user and return their ID
export async function createUser(name: string): Promise<string> {
  const response = await fetch(`${BASE_URL}/api/users/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create user: ${response.statusText}`);
  }

  const data = await response.json();
  userId = data.id;
  return data.id;
}

// Get list of all users
export async function getUsers(): Promise<Record<string, string>> {
  const response = await fetch(`${BASE_URL}/api/users/list`);
  if (!response.ok) {
    throw new Error(`Failed to list users: ${response.statusText}`);
  }
  const data = await response.json();
  return data.users;
}

// Send a message to another user
export async function sendMessage(recipientName: string, message: string): Promise<void> {
  if (!userId) {
    throw new Error("User not authenticated");
  }

  const response = await fetch(`${BASE_URL}/api/messages/send`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": userId,
    },
    body: JSON.stringify({
      recipient_name: recipientName,
      message,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`);
  }
}

// Connect to the WebSocket and set up message handling
export async function connectToChat(
  userId: string,
  onMessage: (message: MessageDelivery) => void
): Promise<void> {
  if (!userId) {
    throw new Error("User not authenticated");
  }

  messageCallback = onMessage;
  ws = new WebSocket(WS_URL);

  return new Promise<void>((resolve, reject) => {
    if (!ws) return reject(new Error("WebSocket not initialized"));

    ws.onopen = () => {
      try {
        // Send authentication message with user ID
        ws?.send(JSON.stringify({ id: userId }));

        // Wait for connection acknowledgment
        ws!.onmessage = (event: MessageEvent) => {
          const data = JSON.parse(event.data);
          if (data.type === "connection_status") {
            // Setup message handler for future messages
            ws!.onmessage = (msgEvent: MessageEvent) => {
              const msgData = JSON.parse(msgEvent.data);
              if (!msgData.type && messageCallback) {
                messageCallback(msgData as MessageDelivery);
              }
            };
            resolve();
          }
        };
      } catch (error) {
        reject(error);
      }
    };

    ws.onerror = (event: Event) => {
      reject(new Error("WebSocket connection failed"));
    };
  });
}

// Disconnect from the chat
export function disconnect(): void {
  if (ws) {
    ws.close();
    ws = null;
  }
  messageCallback = null;
}

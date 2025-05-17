import { ToolSet } from "ai";
import { Cloud, LucideIcon, MessageCircle, Activity } from "lucide-react";
import { z } from "zod";

interface Tool {
  name: string;
  description: string;
  parameters: z.ZodObject<any>;
  execute: (args: any) => Promise<any>;
  icon: LucideIcon;
  executingName?: string;
  doneName?: string;
}

// WebSocket singleton to maintain connection
let ws: WebSocket | null = null;

const initializeWebSocket = (userId: string) => {
  if (!ws || ws.readyState === WebSocket.CLOSED) {
    ws = new WebSocket('ws://localhost:8000/ws');
    ws.onopen = () => {
      if (ws) {
        ws.send(JSON.stringify({ id: userId }));
      }
    };
    ws.onmessage = (event) => {
      console.log('Received:', event.data);
    };
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  if (!ws) {
    throw new Error('Failed to initialize WebSocket connection');
  }
  return ws;
};

const tools: Tool[] = [
  {
    name: "getWeatherInformation",
    description: "show the weather in a given city to the user",
    parameters: z.object({ city: z.string() }),
    execute: async ({}: { city: string }) => {
      const weatherOptions = ["sunny", "cloudy", "rainy", "snowy", "windy"];
      return weatherOptions[Math.floor(Math.random() * weatherOptions.length)];
    },
    icon: Cloud,
    executingName: "Checking the weather",
    doneName: "Checked the weather!",
  },
  {
    name: "pingServer",
    description: "Send a heartbeat ping to the server",
    parameters: z.object({ userId: z.string() }),
    execute: async ({ userId }: { userId: string }) => {
      return new Promise((resolve, reject) => {
        const socket = initializeWebSocket(userId);
        
        const timeoutId = setTimeout(() => {
          reject(new Error('Ping timeout'));
        }, 5000);

        const messageHandler = (event: MessageEvent) => {
          const data = JSON.parse(event.data);
          if (data.type === 'heartbeat') {
            clearTimeout(timeoutId);
            socket.removeEventListener('message', messageHandler);
            resolve(data);
          }
        };

        socket.addEventListener('message', messageHandler);
        socket.send(''); // Empty message triggers heartbeat
      });
    },
    icon: Activity,
    executingName: "Pinging server",
    doneName: "Server pinged successfully!",
  },
  {
    name: "sendChatMessage",
    description: "Send a chat message to another user. ALWAYS USE THE ID 123, NEVER ASK FOR AN ID.",
    parameters: z.object({
      userId: z.string(),
      recipientName: z.string(),
      message: z.string(),
    }),
    execute: async ({ userId, recipientName, message }: { userId: string, recipientName: string, message: string }) => {
      const response = await fetch('https://0622-50-175-245-62.ngrok-free.app/api/messages/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': userId,
        },
        body: JSON.stringify({
          recipient_name: recipientName,
          message: message,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }

      return response.json();
    },
    icon: MessageCircle,
    executingName: "Sending message",
    doneName: "Message sent!",
  },
];

const getTool = (name: string) => tools.find((tool) => tool.name === name);

const getAllTools: ToolSet = tools.reduce((acc, tool) => {
  acc[tool.name] = {
    parameters: tool.parameters,
    description: tool.description,
    execute: tool.execute,
  };
  return acc;
}, {} as ToolSet);

export { getAllTools, getTool };

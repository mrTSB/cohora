"use client";

import { useEffect, useState } from "react";
import { connectToChat, disconnect } from "../api/communicator";
import { MessageDelivery } from "../api/communicator";

export default function ListenPage() {
  const [messages, setMessages] = useState<MessageDelivery[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const userId = "7c03880c-d64f-4115-b9ee-2300a64ebb81";
  useEffect(() => {
    const setupConnection = async () => {
      try {
        await connectToChat(userId, (message) => {
          setMessages((prev) => [...prev, message]);
        });

        setIsConnected(true);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to connect");
        setIsConnected(false);
      }
    };

    setupConnection();

    return () => {
      disconnect();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold">Message Listener</h1>
            <div className="flex items-center">
              <div
                className={`w-3 h-3 rounded-full mr-2 ${
                  isConnected ? "bg-green-500" : "bg-red-500"
                }`}
              />
              <span className="text-sm text-gray-600">
                {isConnected ? "Connected" : "Disconnected"}
              </span>
            </div>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <div className="space-y-4">
            {messages.map((msg, index) => (
              <div key={msg.message_id || index} className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-semibold text-gray-800">{msg.from}</span>
                  <span className="text-sm text-gray-500">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-gray-700 whitespace-pre-wrap">{msg.message}</p>
              </div>
            ))}
          </div>

          {messages.length === 0 && !error && (
            <div className="text-center text-gray-500 py-8">Waiting for messages...</div>
          )}
        </div>
      </div>
    </div>
  );
}

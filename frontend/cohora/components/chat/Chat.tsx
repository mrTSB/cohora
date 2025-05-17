"use client";

import { useUser } from "@clerk/nextjs";
import { TypographyP } from "../ui/prose";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";
import { useChat } from "@ai-sdk/react";
import Image from "next/image";
import { Message } from "ai";
import MCPServerForm from "./MCPServerForm";
import { useState } from "react";
import { getAllTools, type MCPServer } from "@/lib/tools";

interface ChatProps {
  id?: string;
  initialMessages?: Message[];
}

export default function Chat({ id, initialMessages }: ChatProps) {
  const { user } = useUser();
  const [mcpTools, setMcpTools] = useState<typeof getAllTools>({});
  const [mcpServers, setMcpServers] = useState<MCPServer[]>([]);

  const handleAddMCPServer = async (serverData: MCPServer) => {
    console.log("Adding MCP Server", serverData);

    const response = await fetch("/api/mcp-servers", {
      method: "POST",
      body: JSON.stringify(serverData),
    });
    if (response.ok) {
      console.log("MCP Server added", JSON.stringify(serverData));
    }
  };

  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    id,
    initialMessages,
    maxSteps: 20,
  });

  return (
    <div className="flex flex-col max-w-screen-lg h-screen mx-auto w-full">
      <div className="flex-1 overflow-y-auto space-y-6 p-8 mx-auto min-h-0 w-full">
        {messages.length > 0 && (
          <div className="flex flex-1 flex-col justify-start h-full gap-4 w-full">
            {messages.map((message, index) => (
              <ChatMessage key={index} message={message} />
            ))}
          </div>
        )}
        {messages.length === 0 && (
          <div className="flex flex-1 flex-col items-center justify-center h-full">
            <Image
              src="/cohora.svg"
              alt="Cohora Logo"
              width={408}
              height={146}
              className="animate-fade-in"
            />
            <div className="text-center space-y-4">
              <h1 className="text-3xl font-light tracking-tight">Hey, {user?.firstName}</h1>
              <p className="text-muted-foreground text-lg tracking-tight">
                Have your people talk to my people
              </p>
              <MCPServerForm onSubmit={handleAddMCPServer} onCancel={() => {}} />
            </div>
          </div>
        )}
      </div>

      <ChatInput
        input={input}
        handleInputChange={handleInputChange}
        handleSubmit={handleSubmit}
        isLoading={isLoading}
      />
    </div>
  );
}

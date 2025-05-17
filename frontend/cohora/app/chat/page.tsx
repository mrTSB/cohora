"use client";

import { ToolInvocation } from "ai";
import { useChat } from "@ai-sdk/react";
import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";
import Chat from "@/components/chat/Chat";

export default function ChatPage() {
  return (
    <div className="flex flex-col h-full w-full mx-auto">
      <Chat />
    </div>
  );
}

"use client";

import { TypographyP } from "../ui/prose";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";
import { useChat } from "@ai-sdk/react";
import Image from "next/image";

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    maxSteps: 20,
  });
  return (
    <div className="flex flex-col max-w-screen-lg h-screen mx-auto w-full">
      <div className="flex-1 overflow-y-auto space-y-6 p-8 mx-auto min-h-0 w-full">
        {messages.length > 0 && (
          <div className="flex flex-1 flex-col justify-start h-full gap-4 w-full">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
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
              <h1 className="text-3xl font-light tracking-tight">
                Have your people talk to my people
              </h1>
              <p className="text-muted-foreground text-lg tracking-tight">
                Cohora is your personal assistant, connecting with other people's personal
                assistants to help you get things done.
              </p>
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

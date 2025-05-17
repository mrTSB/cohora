"use client";

import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useRef, useEffect } from "react";
import { Input } from "../ui/input";

interface ChatInputProps {
  input: string;
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  isLoading?: boolean;
}

export default function ChatInput({
  input,
  handleInputChange,
  handleSubmit,
  isLoading = false,
}: ChatInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const form = e.currentTarget.form;
      if (form) form.requestSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative px-4 pb-4">
      <div className="relative flex items-center w-full mx-auto">
        <Input
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          className="min-h-[44px] max-h-[200px] pr-12 p-6 rounded-full resize-none bg-background focus-visible:ring-primary/30 focus-visible:border-primary hover:border-primary/30"
          disabled={isLoading}
        />
        <Button
          type="submit"
          size="icon"
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full"
          disabled={!input.trim() || isLoading}
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}

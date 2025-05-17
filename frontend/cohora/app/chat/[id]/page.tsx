import { loadChat } from "@/lib/chat-store";
import Chat from "@/components/chat/Chat";

export default async function ChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const messages = await loadChat(id);
  return (
    <div className="flex flex-col h-full w-full mx-auto">
      <Chat id={id} initialMessages={messages} />
    </div>
  );
}

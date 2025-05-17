import { loadChat } from "@/lib/chat-store";
import Chat from "@/components/chat/Chat";
import { currentUser } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function ChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const user = await currentUser();
  if (!user) {
    redirect("/");
  }
  const messages = await loadChat(user.id, id);
  return (
    <div className="flex flex-col h-full w-full mx-auto">
      <Chat id={id} initialMessages={messages} />
    </div>
  );
}

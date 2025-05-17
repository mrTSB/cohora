import { redirect } from "next/navigation";
import { createChat } from "@/lib/chat-store";
import { currentUser } from "@clerk/nextjs/server";

export default async function Page() {
  const user = await currentUser();
  if (!user) {
    redirect("/");
  }

  const id = await createChat(user.id, user.firstName!); // create a new chat
  redirect(`/chat/${id}`); // redirect to chat page, see below
}

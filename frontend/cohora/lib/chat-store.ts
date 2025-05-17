import { generateId, Message } from "ai";
import { JsonDB } from "./db";
import { getSystemPrompt } from "./prompts";

const db = new JsonDB();

export async function createChat(userId: string, name: string): Promise<string> {
  const id = generateId();
  await db.saveChat(userId, id, [
    {
      role: "system",
      content: getSystemPrompt(name),
    },
  ]);
  return id;
}

export async function loadChat(userId: string, id: string): Promise<Message[]> {
  return db.getChat(userId, id);
}

export async function saveChat({
  userId,
  id,
  messages,
}: {
  userId: string;
  id: string;
  messages: Message[];
}): Promise<void> {
  await db.saveChat(userId, id, messages);
}

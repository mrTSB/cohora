import { existsSync, mkdirSync } from "fs";
import { readFile, writeFile } from "fs/promises";
import path from "path";
import { MCPServer } from "./tools";

interface UserData {
  chats: Record<string, any[]>;
  mcpServers: Record<string, any>;
}

interface Database {
  users: Record<string, UserData>;
}

export class JsonDB {
  private filePath: string;

  constructor(filename: string = "main", directory: string = ".db") {
    const dbDir = path.join(process.cwd(), directory);
    if (!existsSync(dbDir)) mkdirSync(dbDir, { recursive: true });
    this.filePath = path.join(dbDir, `${filename}.json`);
  }

  private async read(): Promise<Database> {
    try {
      const content = await readFile(this.filePath, "utf8");
      return JSON.parse(content);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") {
        return { users: {} };
      }
      throw error;
    }
  }

  private async write(data: Database): Promise<void> {
    const content = JSON.stringify(data, null, 2);
    await writeFile(this.filePath, content);
  }

  async getUserData(userId: string): Promise<UserData> {
    const db = await this.read();
    if (!db.users[userId]) {
      db.users[userId] = { chats: {}, mcpServers: {} };
      await this.write(db);
    }
    return db.users[userId];
  }

  async updateUserData(userId: string, update: Partial<UserData>): Promise<void> {
    const db = await this.read();
    db.users[userId] = { ...db.users[userId], ...update };
    await this.write(db);
  }

  async getChat(userId: string, chatId: string): Promise<any[]> {
    const userData = await this.getUserData(userId);
    return userData.chats[chatId] || [];
  }

  async saveChat(userId: string, chatId: string, messages: any[]): Promise<void> {
    const userData = await this.getUserData(userId);
    userData.chats[chatId] = messages;
    await this.updateUserData(userId, userData);
  }

  async getMcpServers(userId: string): Promise<Record<string, any>> {
    const userData = await this.getUserData(userId);
    return userData.mcpServers;
  }

  async saveMcpServer(userId: string, serverId: string, serverData: MCPServer): Promise<void> {
    console.log("Saving MCP Server", serverData);
    const userData = await this.getUserData(userId);
    userData.mcpServers[serverId] = serverData;
    await this.updateUserData(userId, userData);
  }
}

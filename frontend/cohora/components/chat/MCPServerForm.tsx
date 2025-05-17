import { useState } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog";
import { MCPServer } from "@/lib/tools";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";

interface MCPServerFormProps {
  onSubmit: (serverData: MCPServer) => Promise<void>;
  onCancel: () => void;
}

export default function MCPServerForm({ onSubmit, onCancel }: MCPServerFormProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [command, setCommand] = useState("");
  const [args, setArgs] = useState<string[]>([]);
  const [env, setEnv] = useState<Record<string, string>>({});
  const [transportType, setTransportType] = useState<"stdio" | "sse">("stdio");
  const [transportUrl, setTransportUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await onSubmit({
        name,
        command,
        args,
        env,
        transport: {
          type: transportType,
          ...(transportType === "sse" && { url: transportUrl }),
        },
      });
      setOpen(false);
      setName("");
      setCommand("");
      setArgs([]);
      setEnv({});
      setTransportType("stdio");
      setTransportUrl("");
    } catch (error) {
      console.error("Failed to add MCP server:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">Add MCP Server</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add MCP Server</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Server Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My MCP Server"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="transport">Transport Type</Label>
            <Select
              value={transportType}
              onValueChange={(value: "stdio" | "sse") => setTransportType(value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select transport type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="stdio">STDIO</SelectItem>
                <SelectItem value="sse">SSE</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {transportType === "sse" && (
            <div className="space-y-2">
              <Label htmlFor="transportUrl">SSE URL</Label>
              <Input
                id="transportUrl"
                value={transportUrl}
                onChange={(e) => setTransportUrl(e.target.value)}
                placeholder="https://my-server.com/sse"
                required
              />
            </div>
          )}
          {transportType === "stdio" && (
            <>
              <div className="space-y-2">
                <Label htmlFor="command">Server Command</Label>
                <Input
                  id="command"
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  placeholder="Command to run"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="env">Server Environment Variables</Label>
                <Input
                  id="env"
                  value={JSON.stringify(env)}
                  onChange={(e) => setEnv(JSON.parse(e.target.value))}
                  placeholder="Enter environment variables if required"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="args">Server Arguments</Label>
                <Input
                  id="args"
                  value={args.join(",")}
                  onChange={(e) => setArgs(e.target.value.split(",").map((arg) => arg.trim()))}
                  placeholder="Enter arguments if required"
                />
              </div>
            </>
          )}
          <Button type="submit" disabled={isLoading}>
            {isLoading ? "Adding..." : "Add Server"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

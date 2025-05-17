import { ToolSet } from "ai";
import { Cloud, LucideIcon } from "lucide-react";
import { z } from "zod";

interface Tool {
  name: string;
  description: string;
  parameters: z.ZodObject<any>;
  execute: (args: any) => Promise<any>;
  icon: LucideIcon;
  executingName?: string;
  doneName?: string;
}

const tools: Tool[] = [
  {
    name: "getWeatherInformation",
    description: "show the weather in a given city to the user",
    parameters: z.object({ city: z.string() }),
    execute: async ({}: { city: string }) => {
      const weatherOptions = ["sunny", "cloudy", "rainy", "snowy", "windy"];
      return weatherOptions[Math.floor(Math.random() * weatherOptions.length)];
    },
    icon: Cloud,
    executingName: "Checking the weather",
    doneName: "Checked the weather!",
  },
];

const getTool = (name: string) => tools.find((tool) => tool.name === name);

const getAllTools: ToolSet = tools.reduce((acc, tool) => {
  acc[tool.name] = {
    parameters: tool.parameters,
    description: tool.description,
    execute: tool.execute,
  };
  return acc;
}, {} as ToolSet);

export { getAllTools, getTool };

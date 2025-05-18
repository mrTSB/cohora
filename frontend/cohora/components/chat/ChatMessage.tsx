import { Components } from "react-markdown";
import { solarizedDark as codeTheme } from "react-syntax-highlighter/dist/esm/styles/hljs";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "../ui/button";
import { Check, Copy, Wrench } from "lucide-react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { tool, UIMessage } from "ai";
import { TypographyH2, TypographyH3, TypographyH1, TypographyH4, TypographyP } from "../ui/prose";
import { Card, CardContent } from "../ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../ui/accordion";
import { getTool } from "@/lib/tools";

const customSyntaxTheme = {
  ...codeTheme,
  'pre[class*="language-"]': {
    ...codeTheme['pre[class*="language-"]'],
    background: "hsl(var(--muted))",
    borderRadius: "0.5rem",
    fontFamily: "var(--font-mono)",
    textShadow: "none",
    padding: "1rem",
    margin: "1rem 0",
  },
  'code[class*="language-"]': {
    ...codeTheme['code[class*="language-"]'],
    background: "none",
    fontFamily: "var(--font-mono)",
    textShadow: "none",
    fontSize: "0.875rem",
    padding: "0.5rem",
  },
};

/**
 * Renders markdown content into React components
 * @param content - Markdown string to render
 * @returns JSX Element with rendered markdown
 */
const renderMarkdown = (content: string, key: string): React.ReactNode => {
  // Define custom components for all markdown elements
  const components: Components = {
    // Text components
    p: ({ children }) => <TypographyP>{children}</TypographyP>,
    h1: ({ children }) => <TypographyH1>{children}</TypographyH1>,
    h2: ({ children }) => <TypographyH2>{children}</TypographyH2>,
    h3: ({ children }) => <TypographyH3>{children}</TypographyH3>,
    h4: ({ children }) => <TypographyH4>{children}</TypographyH4>,

    // Lists
    ul: ({ children }) => <ul className="text-sm my-2 pl-6 list-disc">{children}</ul>,
    ol: ({ children }) => <ol className="text-sm my-2 pl-6 list-decimal">{children}</ol>,
    li: ({ children }) => <li className="my-0.5">{children}</li>,

    // Inline formatting
    strong: ({ children }) => <strong className="font-bold">{children}</strong>,
    em: ({ children }) => <em className="italic">{children}</em>,
    del: ({ children }) => <del className="line-through">{children}</del>,

    // Block elements
    blockquote: ({ children }) => (
      <blockquote className="pl-4 border-l-4 border-border my-2 italic text-muted-foreground">
        {children}
      </blockquote>
    ),
    hr: () => <hr className="my-4 border-t border-border" />,

    // Tables
    table: ({ children }) => (
      <div className="overflow-x-auto my-4">
        <table className="min-w-full divide-y divide-border border border-border">{children}</table>
      </div>
    ),
    thead: ({ children }) => <thead className="bg-muted/50">{children}</thead>,
    tbody: ({ children }) => <tbody className="divide-y divide-border">{children}</tbody>,
    tr: ({ children }) => <tr>{children}</tr>,
    th: ({ children }) => (
      <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
        {children}
      </th>
    ),
    td: ({ children }) => <td className="px-3 py-2 whitespace-nowrap text-sm">{children}</td>,

    // Links and images
    a: ({ children, href, title }) => (
      <a
        href={href}
        title={title}
        className="text-primary hover:underline"
        target={href?.startsWith("http") ? "_blank" : undefined}
        rel={href?.startsWith("http") ? "noopener noreferrer" : undefined}
      >
        {children}
      </a>
    ),
    img: ({ src, alt, title }) => (
      <img
        src={src || ""}
        alt={alt || ""}
        title={title || alt || ""}
        className="max-w-full h-auto my-2 rounded-lg blur-in"
      />
    ),

    // Code blocks and inline code
    code: ({ className, children }) => {
      const match = /language-(\w+)/.exec(className || "");
      const isInline = !match;
      return !isInline && match ? (
        <div className="relative group">
          <Button
            onClick={() => {
              navigator.clipboard.writeText(String(children));
              const button = document.activeElement as HTMLButtonElement;
              if (button) {
                const originalContent = button.innerHTML;
                button.innerHTML =
                  '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-green-500"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                setTimeout(() => {
                  button.innerHTML = originalContent;
                }, 1000);
              }
            }}
            variant="ghost"
            size="icon"
            className="absolute right-2 top-2 opacity-100"
            title="Copy code"
          >
            <Copy className="h-2 w-2" />
          </Button>
          <SyntaxHighlighter
            language={match[1]}
            style={customSyntaxTheme}
            PreTag="div"
            className="rounded-lg border border-border bg-background shadow-sm p-4"
          >
            {String(children).replace(/\n$/, "")}
          </SyntaxHighlighter>
        </div>
      ) : (
        <code className="bg-muted px-1.5 py-0.5 rounded-md text-sm text-primary font-mono w-fit">
          {children}
        </code>
      );
    },
    pre: ({ children }) => <>{children}</>,
  };

  return (
    <ReactMarkdown
      key={key}
      components={components}
      remarkPlugins={[remarkGfm]} // Enables GitHub Flavored Markdown support
    >
      {content}
    </ReactMarkdown>
  );
};

interface ToolInvocation {
  toolName: string;
  state: "partial-call" | "call" | "result";
  args?: Record<string, any>;
  result?: string;
}

interface ToolCallProps {
  key: string;
  toolCall: ToolInvocation;
  onResult?: (result: string) => void;
}

function ToolCall({ toolCall, onResult, key }: ToolCallProps) {
  const { toolName, state, args, result } = toolCall;

  switch (state) {
    case "partial-call":
      return (
        <Card className="bg-muted/50">
          <CardContent className="p-4">
            <pre className="text-sm">{JSON.stringify(toolCall, null, 2)}</pre>
          </CardContent>
        </Card>
      );
    case "call":
      const currentTool = getTool(toolName);
      return (
        <Accordion type="single" collapsible>
          <AccordionItem value="tool-call" className="bg-muted rounded-xl px-6 py-2 mt-2">
            <AccordionTrigger className="flex items-center gap-2 hover:no-underline">
              <div className="flex items-center gap-2">
                {currentTool?.icon ? (
                  <currentTool.icon className="w-4 h-4" />
                ) : (
                  <Wrench className="w-4 h-4" />
                )}
                <span className="font-medium">
                  {currentTool?.executingName || "Calling " + toolName}
                </span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-2">
              <pre className="text-sm">{JSON.stringify(toolCall.args, null, 2)}</pre>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      );
    case "result":
      const curTool = getTool(toolName);
      return (
        <Accordion type="single" collapsible>
          <AccordionItem value="tool-result" className="bg-muted rounded-xl px-6 py-2 mt-2">
            <AccordionTrigger className="flex items-center gap-2 hover:no-underline">
              <div className="flex items-center gap-2">
                {curTool?.icon ? (
                  <curTool.icon className="w-4 h-4 text-green-500" />
                ) : (
                  <Check className="w-4 h-4 text-green-500" />
                )}
                <span className="font-medium">{curTool?.doneName ?? "Called " + toolName}</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-2">
              {typeof result === "object" && "isError" in result && result.isError ? (
                <p className="text-sm bg-red-500/10 text-red-500 p-2 rounded-md">
                  {result.content.map((content: any) => content.text).join("\n")}
                </p>
              ) : typeof result === "object" && "content" in result ? (
                <p className="text-sm">
                  {result.content.map((content: any) => content.text).join("\n")}
                </p>
              ) : toolName === "listenForResponse" ? (
                <div className="flex flex-col gap-2">
                  <p className="text-sm font-bold">{result?.from} says:</p>
                  <p className="text-md">{result?.message}</p>
                </div>
              ) : toolName === "sendChatMessage" ? (
                <div className="flex flex-col gap-2">
                  <p className="text-sm font-bold">Sent message to {result?.recipientName}:</p>
                  <p className="text-md">{result?.message}</p>
                </div>
              ) : (
                <p className="text-sm">{JSON.stringify(result)}</p>
              )}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      );
    default:
      return null;
  }
}

export default function ChatMessage(props: { message: UIMessage }) {
  const { message } = props;

  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  return isUser ? (
    <div
      key={message.id}
      className="flex flex-col gap-2 p-4 py-2 rounded-2xl bg-primary text-primary-foreground max-w-md ml-auto shadow-sm w-fit"
    >
      {message.content}
    </div>
  ) : isAssistant ? (
    <div key={message.id} className="flex flex-col gap-2 p-4">
      {message.parts.map((part: any) => {
        switch (part.type) {
          case "text":
            return renderMarkdown(part.text, part.id);
          case "tool-invocation":
            return <ToolCall key={part.id} toolCall={part.toolInvocation} />;
          case "tool-result":
            return <ToolCall key={part.id} toolCall={part.toolResult} />;
          case "result":
            return <ToolCall key={part.id} toolCall={part.result} />;
          default:
            return null;
        }
      })}
    </div>
  ) : (
    <div></div>
  );
}

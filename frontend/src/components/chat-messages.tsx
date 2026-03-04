"use client";

import { useEffect, useRef } from "react";
import { Bot, FileText, Loader2, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { SourceChunk } from "@/types/chat";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sourceChunks?: SourceChunk[];
}

interface ChatMessagesProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}

export function ChatMessages({ messages, isStreaming }: ChatMessagesProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-md space-y-3">
          <Bot className="h-12 w-12 text-muted-foreground mx-auto" />
          <h3 className="text-lg font-medium">Start a conversation</h3>
          <p className="text-sm text-muted-foreground">
            Select documents and ask questions about their content. DocuChat
            will answer using information from your uploaded documents.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto py-6 px-4 space-y-6">
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            isLast={i === messages.length - 1}
            isStreaming={isStreaming}
          />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

function MessageBubble({
  message,
  isLast,
  isStreaming,
}: {
  message: ChatMessage;
  isLast: boolean;
  isStreaming: boolean;
}) {
  const isUser = message.role === "user";
  const showTyping = isLast && isStreaming && !message.content;

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : ""}`}>
      {!isUser && (
        <div className="shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
          <Bot className="h-4 w-4 text-primary" />
        </div>
      )}
      <div
        className={`flex flex-col gap-2 max-w-[80%] ${isUser ? "items-end" : ""}`}
      >
        <div
          className={`rounded-lg px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-muted"
          }`}
        >
          {showTyping ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            message.content
          )}
        </div>
        {message.sourceChunks && message.sourceChunks.length > 0 && (
          <SourceChips chunks={message.sourceChunks} />
        )}
      </div>
      {isUser && (
        <div className="shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
          <User className="h-4 w-4 text-muted-foreground" />
        </div>
      )}
    </div>
  );
}

function SourceChips({ chunks }: { chunks: SourceChunk[] }) {
  // Deduplicate by filename + page
  const unique = new Map<string, SourceChunk>();
  for (const chunk of chunks) {
    const key = `${chunk.filename}-${chunk.page_number}`;
    if (!unique.has(key)) {
      unique.set(key, chunk);
    }
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {Array.from(unique.values()).map((chunk) => (
        <Badge
          key={`${chunk.chunk_id}`}
          variant="outline"
          className="text-xs gap-1 font-normal"
        >
          <FileText className="h-3 w-3" />
          {chunk.filename}, p.{chunk.page_number}
        </Badge>
      ))}
    </div>
  );
}

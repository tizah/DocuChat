"use client";

import { useState } from "react";
import { MessageSquarePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ChatInput } from "@/components/chat-input";
import { ChatMessages } from "@/components/chat-messages";
import { DocumentSelector } from "@/components/document-selector";
import { UploadZone } from "@/components/upload-zone";
import { useChat } from "@/hooks/use-chat";

export default function ChatPage() {
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const { messages, isStreaming, sendMessage, resetChat } = useChat();

  const handleSend = (message: string) => {
    sendMessage(message, selectedDocIds);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-3 shrink-0">
        <h1 className="text-lg font-semibold">Chat</h1>
        {messages.length > 0 && (
          <Button variant="outline" size="sm" onClick={resetChat}>
            <MessageSquarePlus className="h-4 w-4 mr-1.5" />
            New Chat
          </Button>
        )}
      </div>

      <div className="flex flex-1 min-h-0">
        {/* Sidebar - Document selector + Upload */}
        <div className="w-64 border-r hidden md:flex md:flex-col overflow-y-auto shrink-0">
          <div className="p-4 space-y-4">
            <DocumentSelector
              selectedIds={selectedDocIds}
              onSelectionChange={setSelectedDocIds}
            />
            <Separator />
            <UploadZone />
            <Separator />
            <p className="text-xs text-muted-foreground">
              Select documents to use as context for your questions.
            </p>
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0 min-h-0">
          <ChatMessages messages={messages} isStreaming={isStreaming} />
          <ChatInput
            onSend={handleSend}
            disabled={selectedDocIds.length === 0}
            isStreaming={isStreaming}
          />
        </div>
      </div>
    </div>
  );
}

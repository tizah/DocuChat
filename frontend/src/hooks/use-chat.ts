"use client";

import { useCallback, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { ChatMetadata, ChatRequest, SourceChunk } from "@/types/chat";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sourceChunks?: SourceChunk[];
}

interface UseChatReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  conversationId: string | null;
  sendMessage: (message: string, documentIds: string[]) => Promise<void>;
  resetChat: () => void;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (message: string, documentIds: string[]) => {
      if (isStreaming) return;

      // Add user message
      setMessages((prev) => [...prev, { role: "user", content: message }]);
      setIsStreaming(true);

      // Add placeholder for assistant
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const body: ChatRequest = {
          message,
          document_ids: documentIds,
          ...(conversationId ? { conversation_id: conversationId } : {}),
        };

        const response = await fetch(
          `${api.defaults.baseURL}/chat`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail?.message || "Chat request failed");
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response stream");

        const decoder = new TextDecoder();
        let buffer = "";
        let currentSourceChunks: SourceChunk[] | undefined;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("event:")) {
              const eventType = line.slice(6).trim();

              // Find the next data line
              const dataLineIndex = lines.indexOf(line) + 1;
              if (dataLineIndex < lines.length) {
                const dataLine = lines[dataLineIndex];
                if (dataLine?.startsWith("data:")) {
                  const data = dataLine.slice(5).trim();
                  handleSSEEvent(
                    eventType,
                    data,
                    setMessages,
                    setConversationId,
                    (chunks) => {
                      currentSourceChunks = chunks;
                    },
                  );
                }
              }
            }
          }
        }

        // Attach source chunks to the last assistant message
        if (currentSourceChunks) {
          setMessages((prev) => {
            const updated = [...prev];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg?.role === "assistant") {
              updated[updated.length - 1] = {
                ...lastMsg,
                sourceChunks: currentSourceChunks,
              };
            }
            return updated;
          });
        }
      } catch (error: unknown) {
        if (error instanceof Error && error.name === "AbortError") return;
        const errorMessage =
          error instanceof Error ? error.message : "An error occurred";
        setMessages((prev) => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg?.role === "assistant") {
            updated[updated.length - 1] = {
              ...lastMsg,
              content: `Error: ${errorMessage}`,
            };
          }
          return updated;
        });
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [conversationId, isStreaming],
  );

  const resetChat = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setConversationId(null);
    setIsStreaming(false);
  }, []);

  return { messages, isStreaming, conversationId, sendMessage, resetChat };
}

function handleSSEEvent(
  eventType: string,
  data: string,
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>,
  setConversationId: React.Dispatch<React.SetStateAction<string | null>>,
  onSourceChunks: (chunks: SourceChunk[]) => void,
) {
  switch (eventType) {
    case "metadata": {
      const metadata: ChatMetadata = JSON.parse(data);
      setConversationId(metadata.conversation_id);
      if (metadata.source_chunks?.length) {
        onSourceChunks(metadata.source_chunks);
      }
      break;
    }
    case "token": {
      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg?.role === "assistant") {
          updated[updated.length - 1] = {
            ...lastMsg,
            content: lastMsg.content + data,
          };
        }
        return updated;
      });
      break;
    }
    case "error": {
      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg?.role === "assistant") {
          updated[updated.length - 1] = {
            ...lastMsg,
            content: `Error: ${data}`,
          };
        }
        return updated;
      });
      break;
    }
  }
}

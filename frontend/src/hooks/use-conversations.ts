"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ConversationListResponse } from "@/types/chat";

export function useConversations() {
  return useQuery<ConversationListResponse>({
    queryKey: ["conversations"],
    queryFn: async () => {
      const { data } = await api.get<ConversationListResponse>(
        "/conversations",
      );
      return data;
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (conversationId: string) => {
      await api.delete(`/conversations/${conversationId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

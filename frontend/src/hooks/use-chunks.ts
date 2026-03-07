"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ChunkListResponse, ChunkWithContext } from "@/types/document";

export function useChunkWithContext(chunkId: string | null) {
  return useQuery<ChunkWithContext>({
    queryKey: ["chunk-context", chunkId],
    queryFn: async () => {
      const { data } = await api.get<ChunkWithContext>(`/chunks/${chunkId}`);
      return data;
    },
    enabled: !!chunkId,
  });
}

export function useDocumentChunks(documentId: string | null, page?: number) {
  return useQuery<ChunkListResponse>({
    queryKey: ["document-chunks", documentId, page],
    queryFn: async () => {
      const params = page !== undefined ? { page } : {};
      const { data } = await api.get<ChunkListResponse>(
        `/documents/${documentId}/chunks`,
        { params },
      );
      return data;
    },
    enabled: !!documentId,
  });
}

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Document, DocumentListResponse, DocumentStatus } from "@/types/document";
import { isProcessing } from "@/types/document";

export function useDocuments() {
  const query = useQuery<DocumentListResponse>({
    queryKey: ["documents"],
    queryFn: async () => {
      const { data } = await api.get<DocumentListResponse>("/documents");
      return data;
    },
  });

  // Poll every 2 seconds if any document is still processing
  const hasProcessing = query.data?.documents.some((d) => isProcessing(d.status));

  return useQuery<DocumentListResponse>({
    queryKey: ["documents"],
    queryFn: async () => {
      const { data } = await api.get<DocumentListResponse>("/documents");
      return data;
    },
    refetchInterval: hasProcessing ? 2000 : false,
  });
}

export function useDocument(documentId: string) {
  return useQuery<Document>({
    queryKey: ["document", documentId],
    queryFn: async () => {
      const { data } = await api.get<Document>(`/documents/${documentId}`);
      return data;
    },
  });
}

export function useDocumentStatus(documentId: string | null) {
  return useQuery<DocumentStatus>({
    queryKey: ["document-status", documentId],
    queryFn: async () => {
      const { data } = await api.get<DocumentStatus>(`/documents/${documentId}/status`);
      return data;
    },
    enabled: !!documentId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && isProcessing(status) ? 2000 : false;
    },
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation<Document, Error, { file: File; onProgress?: (pct: number) => void }>({
    mutationFn: async ({ file, onProgress }) => {
      const formData = new FormData();
      formData.append("file", file);

      const { data } = await api.post<Document>("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (event) => {
          if (event.total && onProgress) {
            onProgress(Math.round((event.loaded * 100) / event.total));
          }
        },
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`/documents/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

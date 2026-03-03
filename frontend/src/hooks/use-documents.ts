"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Document, DocumentListResponse } from "@/types/document";

export function useDocuments() {
  return useQuery<DocumentListResponse>({
    queryKey: ["documents"],
    queryFn: async () => {
      const { data } = await api.get<DocumentListResponse>("/documents");
      return data;
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

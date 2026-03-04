export interface Document {
  id: string;
  filename: string;
  file_type: string;
  size_bytes: number;
  status: string;
  error_message: string | null;
  page_count: number | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export interface DocumentStatus {
  id: string;
  status: string;
  error_message: string | null;
  page_count: number | null;
  chunk_count: number;
}

export const PROCESSING_STATUSES = [
  "uploaded",
  "extracting",
  "chunking",
  "embedding",
] as const;

export function isProcessing(status: string): boolean {
  return (PROCESSING_STATUSES as readonly string[]).includes(status);
}

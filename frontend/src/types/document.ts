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

export interface Chunk {
  id: string;
  document_id: string;
  chunk_index: number;
  page_number: number;
  content: string;
  token_count: number;
}

export interface ChunkListResponse {
  chunks: Chunk[];
  total: number;
  document_id: string;
}

export interface ChunkWithContext {
  chunk: Chunk;
  previous_chunk: Chunk | null;
  next_chunk: Chunk | null;
  document_filename: string;
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

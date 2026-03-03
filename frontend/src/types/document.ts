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

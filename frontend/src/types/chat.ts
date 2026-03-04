export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  source_chunks: string | null;
  created_at: string;
}

export interface SourceChunk {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_number: number;
  score: number;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}

export interface ChatRequest {
  message: string;
  document_ids: string[];
  conversation_id?: string;
}

export interface ChatMetadata {
  conversation_id: string;
  source_chunks: SourceChunk[];
}

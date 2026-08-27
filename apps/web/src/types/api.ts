export type User = { id: string; email: string; display_name?: string | null };
export type Conversation = { id: string; title: string; archived: boolean; created_at: string; updated_at: string };
export type Message = { id: string; conversation_id: string; role: 'user' | 'assistant' | 'system'; content: string; status: string; created_at: string; updated_at: string };
export type Settings = { preferred_model?: string | null; response_style: 'concise' | 'balanced' | 'detailed' };
export type StreamEvent = { type: 'response.started' | 'text.delta' | 'response.completed' | 'error'; data?: string | null; message_id?: string | null };

import type { Conversation, Message, Settings, StreamEvent, User } from '../../types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
let token = localStorage.getItem('assistant.token') ?? '';

export function setToken(next: string) {
  token = next;
  localStorage.setItem('assistant.token', next);
}

function headers(json = true): HeadersInit {
  return {
    ...(json ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...headers(init?.body !== undefined), ...init?.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? `Request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  async login(email: string, password: string) {
    const data = await request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setToken(data.access_token);
    return data;
  },
  me: () => request<User>('/me'),
  conversations: () => request<Conversation[]>('/conversations'),
  createConversation: (title?: string) =>
    request<Conversation>('/conversations', { method: 'POST', body: JSON.stringify({ title }) }),
  messages: (id: string) => request<Message[]>(`/conversations/${id}/messages`),
  settings: () => request<Settings>('/settings'),
  updateSettings: (settings: Settings) =>
    request<Settings>('/settings', { method: 'PUT', body: JSON.stringify(settings) }),
  async streamMessage(
    conversationId: string,
    content: string,
    onEvent: (event: StreamEvent) => void,
  ) {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/messages/stream`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ content }),
    });
    if (!response.ok || !response.body) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail ?? 'Streaming request failed');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() ?? '';
      for (const raw of events) {
        const line = raw.split('\n').find((item) => item.startsWith('data: '));
        if (line) onEvent(JSON.parse(line.slice(6)) as StreamEvent);
      }
    }
  },
};

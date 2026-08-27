import type { Message } from '../../types/api';

type Draft = { role: 'assistant'; content: string; status: string } | null;

export function MessageList({ messages, draft }: { messages: Message[]; draft: Draft }) {
  if (messages.length === 0 && !draft) {
    return (
      <div className="empty-state">
        <h2>Start a text conversation</h2>
        <p>Phase 1 focuses on secure, persisted streaming text chat. Voice arrives in Phase 2.</p>
      </div>
    );
  }

  return (
    <div className="messages" aria-live="polite">
      {messages.map((message) => (
        <article key={message.id} className={`message ${message.role}`}>
          <strong>{message.role === 'user' ? 'You' : 'Assistant'}</strong>
          <p>{message.content}</p>
          <small>{message.status}</small>
        </article>
      ))}
      {draft ? (
        <article className="message assistant streaming">
          <strong>Assistant</strong>
          <p>{draft.content || 'Thinking…'}</p>
          <small>{draft.status}</small>
        </article>
      ) : null}
    </div>
  );
}

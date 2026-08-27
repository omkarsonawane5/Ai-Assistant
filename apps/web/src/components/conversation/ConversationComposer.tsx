import { FormEvent, KeyboardEvent, useState } from 'react';

export function ConversationComposer({
  disabled,
  onSend,
}: {
  disabled: boolean;
  onSend: (content: string) => Promise<void>;
}) {
  const [content, setContent] = useState('');

  async function sendCurrent() {
    const next = content.trim();
    if (!next || disabled) return;
    setContent('');
    await onSend(next);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    await sendCurrent();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void sendCurrent();
    }
  }

  return (
    <form className="composer" onSubmit={submit}>
      <label className="sr-only" htmlFor="message">
        Message
      </label>
      <textarea
        id="message"
        value={content}
        onChange={(event) => setContent(event.target.value)}
        placeholder="Type a message…"
        onKeyDown={handleKeyDown}
      />
      <button disabled={disabled || !content.trim()} type="submit">
        {disabled ? 'Generating…' : 'Send'}
      </button>
    </form>
  );
}

import { useEffect, useRef, useState } from 'react';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { ConversationComposer } from '../components/conversation/ConversationComposer';
import { ConversationSidebar } from '../components/conversation/ConversationSidebar';
import { MessageList } from '../components/conversation/MessageList';
import { api } from '../services/api/client';
import type { Conversation, Message, Settings } from '../types/api';
import type { VoiceState } from '../types/realtime';
import { AudioPlaybackQueue } from '../services/realtime/AudioPlaybackQueue';
import { MicrophoneCapture } from '../services/realtime/MicrophoneCapture';
import { RealtimeClient } from '../services/realtime/RealtimeClient';
import { VoiceControls } from '../components/conversation/VoiceControls';

type AssistantDraft = { role: 'assistant'; content: string; status: string } | null;

export function AssistantPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [draft, setDraft] = useState<AssistantDraft>(null);
  const [settings, setSettings] = useState<Settings>({ response_style: 'balanced' });
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [transcript, setTranscript] = useState('');
  const realtime = useRef<RealtimeClient | null>(null);
  const microphone = useRef(new MicrophoneCapture());
  const playback = useRef(new AudioPlaybackQueue());
  const turn = useRef<string | null>(null);
  const sequence = useRef(0);

  useEffect(() => () => { microphone.current.stop(); playback.current.clear(); realtime.current?.close(); }, []);

  async function refresh() {
    setLoading(true);
    try {
      const [loadedConversations, loadedSettings] = await Promise.all([
        api.conversations(),
        api.settings(),
      ]);
      setConversations(loadedConversations);
      setSettings(loadedSettings);
      if (!activeId && loadedConversations[0]) setActiveId(loadedConversations[0].id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      return;
    }
    api.messages(activeId).then(setMessages).catch((caught) => {
      setError(caught instanceof Error ? caught.message : 'Failed to load messages');
    });
  }, [activeId]);

  async function newConversation() {
    try {
      const conversation = await api.createConversation('New conversation');
      setConversations((previous) => [conversation, ...previous]);
      setActiveId(conversation.id);
      setMessages([]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to create conversation');
    }
  }

  async function send(content: string) {
    let conversationId = activeId;
    try {
      if (!conversationId) {
        const conversation = await api.createConversation(content.slice(0, 60));
        setConversations((previous) => [conversation, ...previous]);
        conversationId = conversation.id;
        setActiveId(conversationId);
      }

      const optimistic: Message = {
        id: crypto.randomUUID(),
        conversation_id: conversationId,
        role: 'user',
        content,
        status: 'completed',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setMessages((previous) => [...previous, optimistic]);
      setGenerating(true);
      setDraft({ role: 'assistant', content: '', status: 'streaming' });

      await api.streamMessage(conversationId, content, (event) => {
        if (event.type === 'text.delta') {
          setDraft((previous) => ({
            role: 'assistant',
            content: (previous?.content ?? '') + (event.data ?? ''),
            status: 'streaming',
          }));
        }
        if (event.type === 'error') setError(event.data ?? 'Assistant failed');
      });

      setDraft(null);
      setMessages(await api.messages(conversationId));
      setConversations(await api.conversations());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to send message');
    } finally {
      setGenerating(false);
    }
  }

  function updateResponseStyle(response_style: Settings['response_style']) {
    const next = { ...settings, response_style };
    setSettings(next);
    void api.updateSettings(next).catch(() => setError('Failed to save settings'));
  }

  function startVoice() {
    if (!activeId) { setError('Select or create a conversation before starting voice.'); return; }
    const sessionId = crypto.randomUUID(); turn.current = crypto.randomUUID(); sequence.current = 0; setTranscript(''); setVoiceState('CONNECTING');
    realtime.current = new RealtimeClient(sessionId, activeId, (event) => {
      if (event.type === 'session_ready') { setVoiceState('LISTENING'); void microphone.current.start(async (chunk, isFinal) => { const value = await blobToBase64(chunk); if (turn.current) realtime.current?.audio(turn.current, sequence.current++, chunk.type || 'audio/webm', value, isFinal); if (isFinal) setVoiceState('PROCESSING'); }).catch((caught) => { setVoiceState('ERROR'); setError(caught instanceof Error ? caught.message : 'Microphone is unavailable'); }); }
      if (event.type === 'transcript_delta' || event.type === 'transcript_final') setTranscript(event.text);
      if (event.type === 'response_start') { setVoiceState('PROCESSING'); setDraft({ role: 'assistant', content: '', status: 'streaming' }); }
      if (event.type === 'response_text_delta') { setVoiceState('ASSISTANT_SPEAKING'); setDraft((previous) => ({ role: 'assistant', content: (previous?.content ?? '') + event.text, status: 'streaming' })); }
      if (event.type === 'response_audio' && event.turn_id === turn.current) playback.current.enqueue(event.audio_base64, event.mime_type);
      if (event.type === 'response_end') { if (event.status === 'interrupted') playback.current.clear(); setVoiceState(event.status === 'interrupted' ? 'INTERRUPTED' : 'IDLE'); setDraft(null); if (activeId) void api.messages(activeId).then(setMessages); }
      if (event.type === 'session_error') { playback.current.clear(); setVoiceState('ERROR'); setError(event.message); }
    }, (connection) => { if (connection === 'reconnecting') setVoiceState('RECONNECTING'); if (connection === 'closed') setVoiceState('IDLE'); });
    realtime.current.connect();
  }
  function stopVoice() { microphone.current.stop(); }
  function interruptVoice() { if (!turn.current) return; playback.current.clear(); realtime.current?.interrupt(turn.current); setVoiceState('INTERRUPTED'); }

  return (
    <main className="layout">
      <ConversationSidebar
        conversations={conversations}
        activeId={activeId}
        loading={loading}
        onSelect={setActiveId}
        onNew={newConversation}
      />
      <section className="chat">
        <header>
          <div>
            <p className="eyebrow">Text foundation · Phase 1</p>
            <h1>AI Assistant</h1>
          </div>
          <label>
            Style
            <select
              value={settings.response_style}
              onChange={(event) => updateResponseStyle(event.target.value as Settings['response_style'])}
            >
              <option value="concise">Concise</option>
              <option value="balanced">Balanced</option>
              <option value="detailed">Detailed</option>
            </select>
          </label>
        </header>
        <ErrorBanner message={error} onDismiss={() => setError(null)} />
        <VoiceControls state={voiceState} disabled={generating || !activeId} onStart={startVoice} onStop={stopVoice} onInterrupt={interruptVoice} />
        {transcript ? <p className="transcript"><strong>You said:</strong> {transcript}</p> : null}
        <MessageList messages={messages} draft={draft} />
        <ConversationComposer disabled={generating} onSend={send} />
      </section>
    </main>
  );
}

async function blobToBase64(blob: Blob): Promise<string> {
  const bytes = new Uint8Array(await blob.arrayBuffer()); let binary = ''; bytes.forEach((value) => { binary += String.fromCharCode(value); }); return btoa(binary);
}

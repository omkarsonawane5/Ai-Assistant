import { getAccessToken } from '../api/client';
import type { RealtimeServerEvent } from '../../types/realtime';

const id = () => crypto.randomUUID();
export class RealtimeClient {
  private socket: WebSocket | null = null; private attempts = 0; private closed = false; private heartbeat: number | null = null;
  constructor(private sessionId: string, private conversationId: string, private onEvent: (event: RealtimeServerEvent) => void, private onState: (state: 'open' | 'reconnecting' | 'closed') => void) {}
  connect(resume = false) {
    this.closed = false; const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'; const url = base.replace(/^http/, 'ws') + `/realtime/sessions/${this.sessionId}`;
    this.socket = new WebSocket(url, [`bearer.${getAccessToken()}`]);
    this.socket.onopen = () => { this.attempts = 0; this.onState('open'); this.send({ type: 'session_start', conversation_id: this.conversationId, resume }); this.heartbeat = window.setInterval(() => this.send({ type: 'heartbeat' }), 20000); };
    this.socket.onmessage = (message) => this.onEvent(JSON.parse(message.data) as RealtimeServerEvent);
    this.socket.onclose = () => { if (this.heartbeat) window.clearInterval(this.heartbeat); if (!this.closed && this.attempts < 3) { this.onState('reconnecting'); window.setTimeout(() => { this.attempts += 1; this.connect(true); }, 500 * 2 ** this.attempts); } else this.onState('closed'); };
  }
  send(event: Record<string, unknown>) { if (this.socket?.readyState === WebSocket.OPEN) this.socket.send(JSON.stringify({ protocol_version: 1, event_id: id(), ...event })); }
  audio(turnId: string, sequence: number, mimeType: string, audioBase64: string, isFinal: boolean) { this.send({ type: 'audio_input', turn_id: turnId, sequence, mime_type: mimeType.split(';')[0], audio_base64: audioBase64, is_final: isFinal }); }
  interrupt(turnId: string) { this.send({ type: 'interrupt', turn_id: turnId }); }
  close() { this.closed = true; this.send({ type: 'session_end' }); this.socket?.close(); }
}

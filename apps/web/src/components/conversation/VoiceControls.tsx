import type { VoiceState } from '../../types/realtime';
export function VoiceControls({ state, disabled, onStart, onStop, onInterrupt }: { state: VoiceState; disabled: boolean; onStart: () => void; onStop: () => void; onInterrupt: () => void }) {
  const listening = state === 'LISTENING'; const speaking = state === 'ASSISTANT_SPEAKING';
  return <div className="voice-controls"><span aria-live="polite">Voice: {state.toLowerCase().replace('_', ' ')}</span>{listening ? <button type="button" onClick={onStop}>Finish speaking</button> : <button type="button" disabled={disabled} onClick={onStart}>Start voice</button>}{speaking ? <button type="button" onClick={onInterrupt}>Interrupt</button> : null}</div>;
}

export class MicrophoneCapture {
  private recorder: MediaRecorder | null = null;
  async start(onChunk: (data: Blob, isFinal: boolean) => void) {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/wav'].find((type) => MediaRecorder.isTypeSupported(type));
    this.recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    this.recorder.ondataavailable = (event) => { if (event.data.size) onChunk(event.data, false); };
    this.recorder.onstop = () => { stream.getTracks().forEach((track) => track.stop()); onChunk(new Blob([], { type: this.recorder?.mimeType || 'audio/webm' }), true); };
    this.recorder.start(500);
  }
  stop() { if (this.recorder?.state === 'recording') this.recorder.stop(); }
}

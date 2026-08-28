export class AudioPlaybackQueue {
  private queue: Blob[] = [];
  private playing = false;
  private current: HTMLAudioElement | null = null;
  private generation = 0;

  enqueue(base64: string, mimeType: string) {
    const binary = atob(base64); const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
    this.queue.push(new Blob([bytes], { type: mimeType })); void this.playNext(this.generation);
  }
  clear() { this.generation += 1; this.queue = []; this.current?.pause(); this.current = null; this.playing = false; }
  private async playNext(generation: number) {
    if (this.playing || this.queue.length === 0) return;
    this.playing = true; const blob = this.queue.shift()!; const audio = new Audio(URL.createObjectURL(blob)); this.current = audio;
    try { await audio.play(); await new Promise<void>((resolve) => { audio.onended = () => resolve(); audio.onerror = () => resolve(); }); }
    finally { URL.revokeObjectURL(audio.src); if (generation === this.generation) { this.playing = false; this.current = null; void this.playNext(generation); } }
  }
}

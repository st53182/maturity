/**
 * Voice layer — MVP stubs. Swap with Web Speech API or cloud STT/TTS later.
 *
 * @typedef {Object} VoiceProvider
 * @property {() => Promise<boolean>} isAvailable
 * @property {() => Promise<void>} startListening
 * @property {() => Promise<void>} stopListening
 * @property {(text: string) => Promise<void>} speak
 */

/** @type {VoiceProvider} */
export const noopVoiceProvider = {
  async isAvailable() {
    return false;
  },
  async startListening() {
    throw new Error('Speech input is not enabled in this MVP build.');
  },
  async stopListening() {
    /* no-op */
  },
  async speak() {
    throw new Error('Text-to-speech is not enabled in this MVP build.');
  },
};

export function createVoiceProvider() {
  return noopVoiceProvider;
}

import DOMPurify from 'dompurify';
import { marked } from 'marked';

let markedConfigured = false;

function ensureMarked() {
  if (!markedConfigured) {
    marked.use({
      gfm: true,
      breaks: true,
    });
    markedConfigured = true;
  }
}

/**
 * Turn AI markdown into sanitized HTML for v-html.
 */
export function renderAiMarkdown(text) {
  if (!text || typeof text !== 'string') {
    return '';
  }
  ensureMarked();
  try {
    const html = marked.parse(text.trimEnd());
    return DOMPurify.sanitize(html);
  } catch {
    return DOMPurify.sanitize(`<p>${text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>`);
  }
}
